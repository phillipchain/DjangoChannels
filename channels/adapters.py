from django.core.handlers.base import BaseHandler
from django.http import HttpRequest, HttpResponse
from channels import Channel, coreg


class UrlConsumer(object):
    """
    Dispatches channel HTTP requests into django's URL system.
    """

    def __init__(self):
        self.handler = BaseHandler()
        self.handler.load_middleware()

    def __call__(self, **kwargs):
        request = HttpRequest.channel_decode(kwargs)
        try:
            response = self.handler.get_response(request)
        except HttpResponse.ResponseLater:
            return
        Channel(request.response_channel).send(**response.channel_encode())


def view_producer(channel_name):
    """
    Returns a new view function that actually writes the request to a channel
    and abandons the response (with an exception the Worker will catch)
    """
    def producing_view(request):
        Channel(channel_name).send(**request.channel_encode())
        raise HttpResponse.ResponseLater()
    return producing_view


def view_consumer(channel_name):
    """
    Decorates a normal Django view to be a channel consumer.
    Does not run any middleware.
    """
    def inner(func): 
        def consumer(**kwargs):
            request = HttpRequest.channel_decode(kwargs)
            response = func(request)
            Channel(request.response_channel).send(**response.channel_encode())
        coreg.add_consumer(consumer, [channel_name])
        return func
    return inner
