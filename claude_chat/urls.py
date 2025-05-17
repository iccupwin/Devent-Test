from django.urls import path, include
from django.contrib import admin
from django.http import HttpResponse
import time
import sentry_sdk
import os

def trigger_error(request):
    division_by_zero = 1 / 0

def test_performance(request):
    with sentry_sdk.start_transaction(
        op="task",
        name="test_performance",
        sampled=True,
    ) as transaction:
        # Добавляем теги к транзакции
        transaction.set_tag("test_type", "performance")
        transaction.set_tag("environment", os.getenv('DJANGO_ENV', 'development'))
        
        # Имитация тяжелой операции
        time.sleep(1)
        
        # Вложенный спан с метриками
        with sentry_sdk.start_span(
            op="subtask",
            description="heavy_computation",
            sampled=True,
        ) as span:
            # Имитация вычислений
            start_time = time.time()
            result = 0
            for i in range(1000000):
                result += i
            computation_time = time.time() - start_time
            
            # Добавляем метрики к спану
            span.set_data("iterations", 1000000)
            span.set_data("computation_time", computation_time)
            span.set_tag("operation_type", "summation")
            
            time.sleep(0.5)
        
        # Еще один спан с метриками
        with sentry_sdk.start_span(
            op="subtask",
            description="data_processing",
            sampled=True,
        ) as span:
            # Имитация обработки данных
            start_time = time.time()
            data = [i * 2 for i in range(10000)]
            processing_time = time.time() - start_time
            
            # Добавляем метрики к спану
            span.set_data("array_size", len(data))
            span.set_data("processing_time", processing_time)
            span.set_tag("operation_type", "array_processing")
            
            time.sleep(0.3)
        
        # Добавляем общие метрики к транзакции
        transaction.set_data("total_result", result)
        transaction.set_data("final_array_size", len(data))
        
        return HttpResponse(
            f"Performance test completed.<br>"
            f"Result: {result}<br>"
            f"Computation time: {computation_time:.3f}s<br>"
            f"Processing time: {processing_time:.3f}s<br>"
            f"Total time: {time.time() - transaction.start_timestamp:.3f}s"
        )

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    # Тестовые URL для Sentry
    path('sentry-debug/', trigger_error, name='sentry-debug'),
    path('sentry-performance/', test_performance, name='sentry-performance'),
    # Включаем все URL-маршруты из приложения chat
    path('', include('chat.urls')),
]