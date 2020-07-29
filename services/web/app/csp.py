SELF = "'self\'"
UNSAFE = "'unsafe-inline\'"

csp = {
    'font-src': [
        SELF,
        UNSAFE,
        'themes.googleusercontent.com',
        '*.gstatic.com',
        # Google Fonts
        'https://fonts.gstatic.com'
    ],
    'img-src': [
        SELF,
        UNSAFE,
        '*.bootstrapcdn.com',
        '*.googleapis.com',
        'https://www.gravatar.com',
    ],
    'style-src': [
        SELF,
        UNSAFE,
        'stackpath.bootstrapcdn.com',
        'fonts.googleapis.com',
        'ajax.googleapis.com',
        '*.gstatic.com',
        '*',
    ],
    'script-src': [
        SELF,
        UNSAFE,
        'https://maxcdn.bootstrapcdn.com',
        'https://code.jquery.com',
        'https://www.google.com', 
        'ajax.googleapis.com',
    ],
    'frame-src': [
        UNSAFE,
        SELF,
        'www.google.com',
        'www.youtube.com',
    ],
    'default-src': [
        UNSAFE,
        SELF,
    ],
}