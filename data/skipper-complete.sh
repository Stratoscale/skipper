_make_target_extract_script()
{
    local mode="$1"
    shift

    local prefix="$1"
    local prefix_pat=$( command sed 's/[][\,.*^$(){}?+|/]/\\&/g' <<<"$prefix" )
    local basename=${prefix##*/}
    local dirname_len=$(( ${#prefix} - ${#basename} ))

    if [[ $mode == -d ]]; then
        # display mode, only output current path component to the next slash
        local output="\2"
    else
        # completion mode, output full path to the next slash
        local output="\1\2"
    fi

    cat <<EOF
    1,/^# * Make data base/           d;        # skip any makefile output
    /^# * Finished Make data base/,/^# * Make data base/{
                                      d;        # skip any makefile output
    }
    /^# * Variables/,/^# * Files/     d;        # skip until files section
    /^# * Not a target/,/^$/          d;        # skip not target blocks
    /^${prefix_pat}/,/^$/!            d;        # skip anything user dont want

    # The stuff above here describes lines that are not
    #  explicit targets or not targets other than special ones
    # The stuff below here decides whether an explicit target
    #  should be output.

    /^# * File is an intermediate prerequisite/ {
      s/^.*$//;x;                               # unhold target
      d;                                        # delete line
    }

    /^$/ {                                      # end of target block
      x;                                        # unhold target
      /^$/d;                                    # dont print blanks
      s|^\(.\{${dirname_len}\}\)\(.\{${#basename}\}[^:/]*/\{0,1\}\)[^:]*:.*$|${output}|p;
      d;                                        # hide any bugs
    }

    # This pattern includes a literal tab character as \t is not a portable
    # representation and fails with BSD sed
    /^[^#	:%]\{1,\}:/ {         # found target block
      /^\.PHONY:/                 d;            # special target
      /^\.SUFFIXES:/              d;            # special target
      /^\.DEFAULT:/               d;            # special target
      /^\.PRECIOUS:/              d;            # special target
      /^\.INTERMEDIATE:/          d;            # special target
      /^\.SECONDARY:/             d;            # special target
      /^\.SECONDEXPANSION:/       d;            # special target
      /^\.DELETE_ON_ERROR:/       d;            # special target
      /^\.IGNORE:/                d;            # special target
      /^\.LOW_RESOLUTION_TIME:/   d;            # special target
      /^\.SILENT:/                d;            # special target
      /^\.EXPORT_ALL_VARIABLES:/  d;            # special target
      /^\.NOTPARALLEL:/           d;            # special target
      /^\.ONESHELL:/              d;            # special target
      /^\.POSIX:/                 d;            # special target
      /^\.NOEXPORT:/              d;            # special target
      /^\.MAKE:/                  d;            # special target
EOF

    # don't complete with hidden targets unless we are doing a partial completion
    if [[ -z "${prefix_pat}" || "${prefix_pat}" = */ ]]; then
      cat <<EOF
      /^${prefix_pat}[^a-zA-Z0-9]/d             # convention for hidden tgt
EOF
    fi

    cat <<EOF
      h;                                        # hold target
      d;                                        # delete line
    }

EOF
}
__contains_word () {
    local curr_word word=$1; shift

    for curr_word in "$@"; do
        [[ $curr_word == "$word" ]] && return
    done
}


_get_images_from_dockerfiles() {
    local dockerfiles=$( ls Dockerfile.* )	
    for dockerfile in $dockerfiles; do 
        echo ${dockerfile##*.}; 
    done
}

_get_makefile() {
    local words=( "$@" )

    for (( i=0; i < ${#words[@]}; i++ )); do
        if [[ ${words[i]} == -f ]]; then
            echo "${words[i+1]}"
            return
        fi
    done

    echo "Makefile"
}

_skipper_completion() {
    local COMMANDS="build push images rmi run make shell"
    local -A OPTS=(
        [GLOBAL]="-v --verbose --registry --build-container-image --build-container-tag --help"
        [BUILD]="--help"
        [PUSH]="--help"
        [IMAGES]="-r --help"
        [RMI]="-r --help"
        [RUN]="-e --env --help"
        [MAKE]="-e --env -f --help"
    )
    local cur=${COMP_WORDS[$COMP_CWORD]}
    local prev=${COMP_WORDS[$COMP_CWORD-1]}

    if __contains_word "build" ${COMP_WORDS[*]}; then
        images=( $(_get_images_from_dockerfiles) )
        COMPREPLY=( $(compgen -W "${images[*]}" -- $cur) )

    elif __contains_word "push" ${COMP_WORDS[*]}; then
        images=( $(_get_images_from_dockerfiles) )
        COMPREPLY=( $(compgen -W "${images[*]}" -- $cur) )

    elif __contains_word "images" ${COMP_WORDS[*]}; then
        COMPREPLY=( $(compgen -W "${OPTS[IMAGES]}" -- $cur) )

    elif __contains_word "rmi" ${COMP_WORDS[*]}; then
        if [[ $cur == -* ]]; then
            COMPREPLY=( $(compgen -W "${OPTS[RMI]}" -- $cur) )
        else
            images=( $(_get_images_from_dockerfiles) )
            COMPREPLY=( $(compgen -W "${images[*]}" -- $cur) )
        fi

    elif __contains_word "run" ${COMP_WORDS[*]}; then
        COMPREPLY=( $(compgen -W "${OPTS[RUN]}" -- $cur) )

    elif __contains_word "make" ${COMP_WORDS[*]}; then
        if [[ $cur == -* ]]; then
            COMPREPLY=( $(compgen -W "${OPTS[RUN]}" -- $cur) )
        else
            if [[ $prev == -f ]]; then 
                COMPREPLY=( $(compgen -f -X '!*[mM]akefile' -- $cur) )
            else
                makefile=$(_get_makefile ${COMP_WORDS[*]})

                # recognise that possible completions are only going to be displayed
                # so only the base name is shown
                local mode=--
                if (( COMP_TYPE != 9 )); then
                    mode=-d # display-only mode
                fi

                COMPREPLY=( $( LC_ALL=C make -npq __BASH_MAKE_COMPLETION__=1 -f "$makefile" "." .DEFAULT 2>/dev/null | \
                               command sed -nf <(_make_target_extract_script $mode "$cur") ) )
            fi
        fi
    
    else
        if [[ $cur == -* ]]; then
            COMPREPLY=( $(compgen -W "${OPTS[GLOBAL]}" -- $cur) )
        else
            COMPREPLY=( $(compgen -W "$COMMANDS" -- $cur) ) 
        fi
    fi

    return 0
}

complete -F _skipper_completion skipper;
