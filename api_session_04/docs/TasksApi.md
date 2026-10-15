# swagger_client.TasksApi

All URIs are relative to *http://localhost:5000/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_task**](TasksApi.md#create_task) | **POST** /tasks | Tạo task mới
[**delete_task**](TasksApi.md#delete_task) | **DELETE** /tasks/{taskId} | Xóa task
[**get_task_by_id**](TasksApi.md#get_task_by_id) | **GET** /tasks/{taskId} | Lấy task theo ID
[**list_tasks**](TasksApi.md#list_tasks) | **GET** /tasks | Lấy danh sách task
[**patch_task**](TasksApi.md#patch_task) | **PATCH** /tasks/{taskId} | Cập nhật task

# **create_task**
> Task create_task(body)

Tạo task mới

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint


# create an instance of the API class
api_instance = swagger_client.TasksApi(swagger_client.ApiClient(configuration))
body = swagger_client.CreateTaskInput() # CreateTaskInput | 

try:
    # Tạo task mới
    api_response = api_instance.create_task(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling TasksApi->create_task: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**CreateTaskInput**](CreateTaskInput.md)|  | 

### Return type

[**Task**](Task.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_task**
> delete_task(task_id)

Xóa task

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint


# create an instance of the API class
api_instance = swagger_client.TasksApi(swagger_client.ApiClient(configuration))
task_id = '38400000-8cf0-11bd-b23e-10b96e4ef00d' # str | 

try:
    # Xóa task
    api_instance.delete_task(task_id)
except ApiException as e:
    print("Exception when calling TasksApi->delete_task: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **task_id** | [**str**](.md)|  | 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_task_by_id**
> Task get_task_by_id(task_id)

Lấy task theo ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint


# create an instance of the API class
api_instance = swagger_client.TasksApi(swagger_client.ApiClient(configuration))
task_id = '38400000-8cf0-11bd-b23e-10b96e4ef00d' # str | 

try:
    # Lấy task theo ID
    api_response = api_instance.get_task_by_id(task_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling TasksApi->get_task_by_id: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **task_id** | [**str**](.md)|  | 

### Return type

[**Task**](Task.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_tasks**
> TaskPage list_tasks(limit=limit, status=status)

Lấy danh sách task

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint


# create an instance of the API class
api_instance = swagger_client.TasksApi(swagger_client.ApiClient(configuration))
limit = 20 # int | Số task tối đa trả về (optional) (default to 20)
status = swagger_client.TaskStatus() # TaskStatus | Lọc task theo trạng thái (optional)

try:
    # Lấy danh sách task
    api_response = api_instance.list_tasks(limit=limit, status=status)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling TasksApi->list_tasks: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Số task tối đa trả về | [optional] [default to 20]
 **status** | [**TaskStatus**](.md)| Lọc task theo trạng thái | [optional] 

### Return type

[**TaskPage**](TaskPage.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **patch_task**
> Task patch_task(body, task_id)

Cập nhật task

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint


# create an instance of the API class
api_instance = swagger_client.TasksApi(swagger_client.ApiClient(configuration))
body = swagger_client.UpdateTaskInput() # UpdateTaskInput | 
task_id = '38400000-8cf0-11bd-b23e-10b96e4ef00d' # str | 

try:
    # Cập nhật task
    api_response = api_instance.patch_task(body, task_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling TasksApi->patch_task: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**UpdateTaskInput**](UpdateTaskInput.md)|  | 
 **task_id** | [**str**](.md)|  | 

### Return type

[**Task**](Task.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

