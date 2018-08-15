import os

azure = False
try:
    os.environ["MONGO_PASSWORD"]
    azure = True
except KeyError:
    pass

# Database configuration
if azure:
    DEBUG=True
    MONGO_HOST="sweet-ostrich-mongodb.dev.svc.cluster.local"
    MONGO_PORT=27017
    MONGO_DBNAME="eve"
    MONGO_USERNAME="root"
    MONGO_PASSWORD=os.environ["MONGO_PASSWORD"]
    MONGO_AUTH_SOURCE = "admin"
    MONGO_REPLICA_SET = "rsname"
else:
    DEBUG=True
    MONGO_HOST="localhost"
    MONGO_PORT=27017
    MONGO_DBNAME="eve"

# Enable reads (GET), inserts (POST) and DELETE for resources/collections
# (if you omit this line, the API will default to ['GET'] and provide
# read-only access to the endpoint).
RESOURCE_METHODS = ['GET']

# Enable reads (GET), edits (PATCH), replacements (PUT) and deletes of
# individual items  (defaults to read-only item access).
ITEM_METHODS = ['GET']

schema_clara_item = {
    # Schema definition, of the CLARA items.
    'main_scale': {
        'type': 'string',
        'minlength': 1,
        'maxlength': 20,
        'required': True
    },
    'itembank_id': {
        'type': 'string',
        'minlength': 1,
        'maxlength': 4,
        'required': True
    },
    'presenting_order': {
        'type': 'integer',
        'required': True
    },
    'clara_item': {
        'type': 'string',
        'minlength': 1,
        'maxlength': 255,
        'required': True
    },
    'language': {
        'type': 'string',
        'minlength': 2,
        'maxlength': 2,
        'required': True
    },
}

clara_items = {
    # 'title' tag used in item links. Defaults to the resource title minus
    # the final, plural 's' (works fine in most cases but not for 'people')
    # 'item_title': 'person',

    # by default the standard item entry point is defined as
    # '/people/<ObjectId>'. We leave it untouched, and we also enable an
    # additional read-only entry point. This way consumers can also perform
    # GET requests at '/people/<lastname>'.
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'language'
    },

    # We choose to override global cache-control directives for this resource.
    'cache_control': 'max-age=10,must-revalidate',
    'cache_expires': 10,

    # most global settings can be overridden at resource level
    'resource_methods': ['GET', 'POST'],

    'schema': schema_clara_item
}


DOMAIN = {
    'clara_items': clara_items
}
