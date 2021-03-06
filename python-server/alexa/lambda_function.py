import json
import logging
import requests

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response


API_ENDPOINT = ""
VOICE_COMMAND_API = "/api/voice-command"
GET_SENSORS_API = "/api/sensor"
# temporary storing the token inside the skil, will be replaced with some auth logic
API_AUTH_TOKEN = ""
SKILL_NAME = "command home"
HELP_MESSAGE = "You can say do some command, replacing some command with the actual command." \
               "Or ask waht is the temperature and humidity"
HELP_REPROMPT = "What can I help you with?"
LAUNCH_MESSAGE = "Tell me your command"
STOP_MESSAGE = "Goodbye!"
EXCEPTION_MESSAGE = "Sorry. Some problems occured"


sb = SkillBuilder()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        handler_input.response_builder.speak(LAUNCH_MESSAGE).ask("hmm should reprompt")
        return handler_input.response_builder.response


class QuestionsIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("QuestionsIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In QuestionsIntent")
        sensors_map = {"inside": "living", "outside": "outside"}
        sensor = handler_input.request_envelope.request.intent.slots["sensor"].value
        location = handler_input.request_envelope.request.intent.slots["location"].value
        try:
            url = API_ENDPOINT + GET_SENSORS_API + "/" + sensor + "_" + sensors_map[location]
            response = requests.get(url=url, headers=get_auth_header())
            sensor_value = json.loads(response.text)["data"][0]["value"]
            speech = "The {0} is {1}".format(sensor, sensor_value)
        except Exception as e:
            logger.error(str(e))

        handler_input.response_builder.speak(speech).ask("hmm should reprompt")

        return handler_input.response_builder.response

class MyCommandIsHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("MyCommandIsIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In MyCommandIsHandler")
        given_command = handler_input.request_envelope.request.intent.slots["Command"].value
        requests.post(url=API_ENDPOINT + VOICE_COMMAND_API, data={'command': given_command}, headers=get_auth_header())
        speech = "Sending your command: {0}".format(given_command)
        handler_input.response_builder.speak(speech).ask("hmm should reprompt")

        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")

        handler_input.response_builder.speak(HELP_MESSAGE).ask(
            HELP_REPROMPT).set_card(SimpleCard(
                SKILL_NAME, HELP_MESSAGE))
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In CancelOrStopIntentHandler")

        handler_input.response_builder.speak(STOP_MESSAGE)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")

        handler_input.response_builder.speak(HELP_MESSAGE).ask(
            HELP_REPROMPT)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")

        logger.info("Session ended reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.info("In CatchAllExceptionHandler")
        logger.error(exception, exc_info=True)

        handler_input.response_builder.speak(EXCEPTION_MESSAGE).ask(
            HELP_REPROMPT)

        return handler_input.response_builder.response


class RequestLogger(AbstractRequestInterceptor):
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))


class ResponseLogger(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug("Alexa Response: {}".format(response))

def get_auth_header():
    return {'Authorization': 'Bearer ' + API_AUTH_TOKEN}

# Register intent handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(MyCommandIsHandler())
sb.add_request_handler(QuestionsIntent())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Handler name that is used on AWS lambda
lambda_handler = sb.lambda_handler()
