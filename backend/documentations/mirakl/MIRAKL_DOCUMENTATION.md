Mirakl Marketplace APIs
Copy

General Notes
Backward compatibility information
Mirakl solutions are updated through continuous delivery to provide new features, security fixes and bug fixes.

New deployed versions are backward compatible, which guarantees the durability of your integration after a Mirakl solution update, on condition that your integration follows these guidelines:

Your integration must allow for new fields to be added in API responses. From time to time, we add new fields as part of new features.
Do not expect fields to always have the same order in API calls. The order can change when fields are added to APIs.
Your integration must allow for new values to be added in enumeration fields. We can add new values in enumeration fields to support new features. We advise that you use strings to deserialize enumeration fields. Alternatively, you can configure your deserializer to accept unknown enumeration values.
While most of our APIs support XML format, we strongly advise you to use JSON format, as our newest APIs are only available in JSON format.

Should you decide to validate our APIs output using XSD files, please note that your XSD should take into account the guidelines defined above. Mirakl does not provide XSD files for its APIs and does not offer support for writing XSD files.

Undocumented attributes
Some APIs may return more data than indicated in the documentation. Do not rely on this undocumented data, there is no guarantee about it.

Authentication
You can authenticate through API by sending your API key in the Authorization header.

Example:



Authorization: YOUR_API_KEY
HTTPS only
All requests must use the HTTPS protocol.

API return codes
Mirakl API uses standard HTTP return codes.

When making HTTP requests, you can check the success or failure status of your request by using the HTTP Status Codes (i.e. 200). You must not use the HTTP Status Messages or Reason-Phrases (i.e. OK), as they are optional and may not be returned in HTTP responses (see RFC9110 for more information).

Our API documentation does not document Reason-Phrases but provides a short contextualized description of HTTP Status Codes.

Success Codes
200: OK - Request succeeded.
201: Created - Request succeeded and resource created.
202: Accepted - Request accepted for processing.
204: No Content - Request succeeded but does not return any content.
Error Codes
400: Bad Request - Parameter errors or bad method usage. Bad usage of the resource. For example: a required parameter is missing, some parameters use an incorrect format, a data query is not in the expected state.
401: Unauthorized - API call without authentication. Add authentication information or use a valid authentication token.
403: Forbidden - Access to the resource is denied. Current user can not access the resource.
404: Not Found - The resource does not exist. The resource URI or the requested resource do not exist for the current user.
405: Method Not Allowed - The HTTP method (GET, POST, PUT, DELETE) is not allowed for this resource. Refer to the documentation for the list of accepted methods.
406: Not Acceptable - The requested response content type is not available for this resource. Refer to the documentation for the list of correct values of the Accept header for this request.
410: Gone - The resource is permanently gone. The requested resource is no longer available and will not be available again.
415: Unsupported Media Type - The entity content type sent to the server is not supported. Refer to the documentation for the list of correct values of the Content-type header to send data.
429: Too many requests - Rate limits are exceeded. The user has sent too many requests in the last hour. Refer to the documentation for the maximum calls count per hour.
500: Internal Server Error - The server encountered an unexpected error.
Rate limits
Mirakl APIs are protected by rate limits. Each API has a dedicated section displaying its rate limit.

If you make too many calls, you might receive an HTTP 429 "Too Many Requests" error. The response will contain a Retry-After header that specifies the number of seconds to wait before making a new request.

Request Content-Type
If an API request supports multiple Content-Types, add a Content-Type header to select the format to use in the request. The API documentation lists the formats an API can consume.

Response Content-Type
If an API response supports multiple Content-Types, add an Accept header to select the format accepted in the response. The API documentation lists the formats an API can produce.

List of values as URL parameters
array type fields indicate a list of values as URL parameters. You can add more parameter=value elements to the URL. Refer to the example in the right panel.

UTF-8 encoding
Text data is encoded in UTF-8.

Locale
If the API returns internationalized data, you can specify the locale parameter.

The Locale format is usually <ISO-639>_<ISO-3166> (e.g. "en_US"). There are some exceptions where the Locale format can be <ISO-639> (e.g. "en"). The locale returned in a response uses this format.

The APIs only accept locales that are equivalent to the languages activated in the back-office.

Date formats
APIs can use different date formats (compliant with ISO 8601):

date-time with the pattern YYYY-MM-DDThh:mm:ss[.SSS]±hh:mm.
The offset +00:00 can be replaced by Z (the zero UTC offset).
All APIs provide date-times in UTC, with the trailing Z.
Milliseconds may be omitted if equals to .000.
date-time-without-timezone with the pattern YYYY-MM-DDThh:mm:ss[.SSS].
The timezone does not appear.
Milliseconds may be omitted if equals to .000.
time with the pattern hh:mm[:ss][.SSS]±hh:mm. Time only, with timezone
The offset +00:00 can be replaced by Z (the zero UTC offset).
Seconds may be omitted if equals to :00.
Milliseconds may be omitted if equals to .000.
In the patterns:

YYYY: years (four-digit)
MM: months, 01-12 (two-digit)
DD: days, 01-31 (two-digit)
T is a delimiter between the date and time
hh: hours, 00-23 (two-digit)
mm: minutes, 00-59 (two-digit)
ss: seconds, 00-60 (two-digit)
SSS: milliseconds, 000-999 (three-digit)
±hh:mm: refers to an offset from UTC
For GET requests, use URL encoding (for example, 2019-08-29T02:34:00+02:00 becomes 2019-08-29T02%3A34%3A00%2B02%3A00).

Shop Selection
When calling APIs as a shop, a request parameter shop_id is available. This parameter is useful when a user is associated to multiple shops and should be specified to select the shop to be used by the API.

Offset pagination & sort
Some APIs support offset pagination. In this case, you can use the max and offset parameters:

max: The max parameter is used to indicate the maximum number of items returned per page. This parameter is optional. The default value of this parameter is 10. The maximum value of this parameter is 100.
offset: The offset parameter is used to indicate the index of the first item (among all the results) in the returned page. This parameter is optional. The default value of this parameter is 0, which means that no offset is applied.
With pagination, the URL of the previous and/or next page can be returned in the header's attribute Link of the response.

When a sort parameter is available on such an API, it can be used to sort the results.

sort: The parameter sort is used to indicate how the results should be sorted. This parameter is optional. The possible values for this parameter are defined in resources. The default value of this parameter is defined in resources.

order: The parameter order is used to indicate the sort direction. This parameter is optional. The possible values ​​for this parameter are asc (default) or desc.

Seek pagination & sort
For better performance and user experience, some APIs support "seek" pagination. This means that you cannot go directly to the N-th page.

Use the optional limit query parameter to indicate the maximum number of items returned per page. The default value is 10. The maximum value is 100.

If there are more results to return, the response contains a next_page_token field. Pass this value in the page_token query parameter to return the next page of results.

The API also returns a previous_page_token when the result is not the first page. Use it the same way as next_page_token.

Values of next_page_token and previous_page_token contain all required parameters to access next and previous page. When using the page_token parameter all other parameters are ignored, regardless of the value given to page_token.

When a sort parameter is available, it must follow the sort=criterion,direction format where:

criterion is the name of the criterion to sort by (e.g: date_created, title, ...)
direction is the sort direction. Can be one of ASC, DESC