_skipper_completion() {
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   _SKIPPER_COMPLETE=complete $1 ) )
    return 0
}

complete -F _skipper_completion -o default skipper;
