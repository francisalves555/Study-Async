function flip_card(id){
        card = document.getElementById(id)

        if(card.style.display == 'none' || card.style.display == ''){
            card.style.display = 'block'
        }

        else{
            card.style.display = 'none' 
        }
}
