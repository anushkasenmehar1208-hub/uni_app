function _trackVV() {
    var root = document.querySelector('.alex-voice-overlay-root');
    var row = document.getElementById('alex-type-row');
    if(!root) return;
    
    var vv = window.visualViewport;
    if(vv) {
        root.style.setProperty('top', vv.offsetTop + 'px', 'important');
        root.style.setProperty('left', vv.offsetLeft + 'px', 'important');
        root.style.setProperty('width', vv.width + 'px', 'important');
        root.style.setProperty('height', vv.height + 'px', 'important');
        
        // Hide the call row (mic/end buttons) if keyboard is taking up > 15% of screen
        var isKbUp = vv.height < window.innerHeight * 0.85;
        if(isKbUp && document.activeElement === document.getElementById('alex-type-input')) {
            root.classList.add('alex-kb-open');
        } else {
            root.classList.remove('alex-kb-open');
        }
    } else {
        root.style.setProperty('top', '0px', 'important');
        root.style.setProperty('left', '0px', 'important');
        root.style.setProperty('width', '100%', 'important');
        root.style.setProperty('height', window.innerHeight + 'px', 'important');
    }
}
