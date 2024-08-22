#function k --wraps=kubectl --description 'alias k=kubectl'
#  kubectl $argv
#        
#end

function k --wraps=kubectl --description 'alias k=kubectl'
    kubecolor $argv

end
