function hideContent () {
  $(".js-product_section .description").contents().slice( 10).wrapAll( '<span class="more-text"></span>' );
  $($.parseHTML('<a href="javascript:void(0);" class="read-more"><br>Read more...</a> ')).insertBefore(".more-text");
  unhideContent();
}

function unhideContent () {
  $(".read-more").click(function(){
    $(this).siblings(".more-text").contents().unwrap();
    $($.parseHTML('<a href="javascript:void(0);" class="read-less"><br>Read less...</a> ')).appendTo(".description");
    $(this).remove();

    $(".read-less").on('click', function() {
	  $(this).remove();
      hideContent();
    });
  });
}

$(document).ready(function(){

  hideContent();

});
