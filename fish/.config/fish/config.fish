if status is-interactive
    # Commands to run in interactive sessions can go here
end

set -gx EDITOR nvim
set -gx VISUAL nvim
set -gx TERM kitty

function fish_greeting
    echo The time is (set_color yellow; date +%T; set_color normal)
end