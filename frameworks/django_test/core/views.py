from django.http import JsonResponse, HttpResponse
from core.models import ExampleModel
from core.utils import generate_load


def json_test_view(request):
    return JsonResponse({'foo': 'bar'})


def model_test_view(request):
    example, created = ExampleModel.objects.get_or_create(
        foo='bar',
        bar='foo'
    )
    return JsonResponse({'foo': example.foo, 'bar': example.bar})


def load_test_view(request):
    response = generate_load()
    return HttpResponse(response)
