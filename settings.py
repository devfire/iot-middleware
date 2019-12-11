import configparser
import logging
import jsonschema

# set our default log level
LOG_LEVEL = logging.INFO

# set the default config file
CONFIG_FILE = 'settings.ini'

# initialize the config parser
config = configparser.ConfigParser()

'''
In a JSON Schema, by default properties are not required, all that our schema does 
is state what type they must be if the property is present. 

So, for validation to flag whatever additional properties are missing, 
we need to mark that key as a required property first, 
by adding a required list with names. For more info:
https://json-schema.org/understanding-json-schema/reference/object.html#required-properties

NOTE: the "required" property is at the end of the schema.
'''
schema = {
    "type" : "object",
    "properties" : {
        "mac" : {"type" : "string"},
        "feedName" : {"type" : "string"},
        "value" : {"type" : "number"},
    },
    "required": ["mac", "feedName", "value"]
}
