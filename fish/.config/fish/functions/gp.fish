function gp --wraps=git --description 'quick commit git push'
    git add .
    git commit -m "$argv"
    git push

end
