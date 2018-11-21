function typeEffect(element, speed, text) {
	$(element).html('');
	var i = 0;
	var timer = setInterval(function() {
        if (i < text.length) {
            $(element).append(text.charAt(i));
            i++;
        } else {
            clearInterval(timer);
        }
    }, speed);
}