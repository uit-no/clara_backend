schema = {
    # Schema definition, of the possible student classes (studiekull).
    'student_class': {
        'type': 'string',
        'minlength': 1,
        'maxlength': 255,
        'required': True
    },
    'active': {
        'type': 'boolean',
        'default': True
    }
}

student_classes = {
    # We choose to override global cache-control directives for this resource.
    'cache_control': 'max-age=10,must-revalidate',
    'cache_expires': 10,

    # most global settings can be overridden at resource level
    'resource_methods': ['GET'],

    'schema': schema
}
