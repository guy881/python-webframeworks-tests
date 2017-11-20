from django.http import JsonResponse
from core.models import ExampleModel


def json_test_view(request):
	return JsonResponse({'foo': 'bar'})


def model_test_view(request):
	example, created = ExampleModel.objects.get_or_create(
		foo='bar',
		bar='foo'
	)
	return JsonResponse({'foo': example.foo, 'bar': example.bar})

