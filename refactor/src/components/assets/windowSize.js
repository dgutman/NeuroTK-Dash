if (!window.dash_clientside) {
    window.dash_clientside = {};
}
dash_clientside.clientside = {
    update_window_dimensions: function() {
        return {
            width: window.innerWidth,
            height: window.innerHeight
        };
    }
}

window.onresize = function() {
    var height = window.innerHeight || 
        document.documentElement.clientHeight || 
        document.body.clientHeight;

    var width = window.innerWidth || 
        document.documentElement.clientWidth || 
        document.body.clientWidth;

    window.dash_clientside = Object.assign({}, window.dash_clientside, {
        clientside: {
            update_window_dimensions: function() {
 //               console.log(width,height)
                return {'width': width, 'height': height};
            }
        }
    });
};
