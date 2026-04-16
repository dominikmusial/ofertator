# Mirakl Marketplace APIs

{% partial file="/partial-content/product/mmp/rest/seller/openapi-description.md" /%}


## Servers

URL to be replaced by your Mirakl instance URL
```
https://your-instance.mirakl.net
```

## Security

### shop_api_key

Type: apiKey
In: header
Name: Authorization

## Download OpenAPI description

[Mirakl Marketplace APIs](https://developer.mirakl.com/_bundle/content/product/mmp/rest/seller/openapi3.yaml)

## Stores

### A01 - Get shop information

 - [GET /api/account](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/stores/a01.md): Call FrequencyRecommended usage: Once per dayMaximum usage: Once per day

### A02 - Update shop information

 - [PUT /api/account](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/stores/a02.md): Depending on the operator's configuration, some fields might not be editable.Call FrequencyRecommended usage: At each information updateMaximum usage: Once per day

### A21 - Get shop statistics

 - [GET /api/account/statistics](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/stores/a21.md): Call FrequencyRecommended usage: Once per dayMaximum usage: Once per day

### S30 - List shop's documents

 - [GET /api/shops/documents](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/stores/s30.md): You must specify at least one of the following parameters: shop_ids, updated_sinceCall FrequencyRecommended usage: At each display of a page that includes documents from a store (for example: during the KYC process)Maximum usage: At each display of a page that includes documents from a store (for example: during the KYC process)

### S32 - Upload business documents to associate with a shop

 - [POST /api/shops/documents](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/stores/s32.md): Document filenames must be distinct and there can be only one file per document type.Only documents of the following types are supported: csv, doc, docx, gif, html, jpeg, latex, mp4, odp, odc, odg, ods, odt, pdf, png, pps, ppsx, ppt, pptx, quicktime, rtf, text, tiff, xls, xlsx, xml, zipYou can upload a maximum of 50 business documents for each shop. These documents are not order related documents.Call FrequencyRecommended usage: At each business document upload to a shopMaximum usage: 50 business documents per call

### S31 - Download documents for one or multiple shops

 - [GET /api/shops/documents/download](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/stores/s31.md): It is mandatory to specify either the shop_ids or the document_ids.  If a list of document identifiers is specified only these documents are downloaded.          If more than one document id is specified, the documents will be wrapped in a ZIP archive      If only one document id is specified the document will not be zipped            If no document identifiers is specified, all the shop documents will be downloaded.    Use a list of shop document type codes to retrieve specific types from your shop.    In this case, the output of the API will always be a ZIP archive even if there is only one document to retrieve.  When documents are retrieved, they're wrapped into a ZIP archive except when only one document id is specified. The tree structure of this archive is as follow:
documents-timestamp.zip
|__ shop_id/
|   |__ image.png
|   |__ image(1).png
|   |__ foo.txt
Returns a 404 if at least one document id or one document type code is invalidCall FrequencyRecommended usage: After each S30 call, when you want to download documents from a storeMaximum usage: After each S30 call, when you want to download documents from a store

### S33 - Delete a shop document

 - [DELETE /api/shops/documents/{document_id}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/stores/s33.md): Call FrequencyRecommended usage: At each document deletion from one storeMaximum usage: At each document deletion from one store

## Platform Settings

### AF01 - List all custom fields

 - [GET /api/additional_fields](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/af01.md): Call FrequencyRecommended usage: Once per dayMaximum usage: Once per dayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### CH11 - List all enabled channels

 - [GET /api/channels](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/ch11.md): Results are sorted by codeCall FrequencyRecommended usage: Once per dayMaximum usage: Once per dayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### CUR01 - List currency codes and labels

 - [GET /api/currencies](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/cur01.md): List currency codes and labels activated on the platformCall FrequencyRecommended usage: Once per dayMaximum usage: Once per dayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### DO01 - List all document types

 - [GET /api/documents](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/do01.md): Call FrequencyRecommended usage: Once per dayMaximum usage: Once per dayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### L01 - List locale codes and labels

 - [GET /api/locales](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/l01.md): List locale codes and labels from your platform to automate product format exports (API H01, PM01, VL01) from your PIM systemCall FrequencyRecommended usage: Once per dayMaximum usage: Once per day

### OF61 - List offer conditions

 - [GET /api/offers/states](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/of61.md): Sorted by sort index, set in the back-officeCall FrequencyRecommended usage: Once per dayMaximum usage: Once per dayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### PC01 - List platform configurations

 - [GET /api/platform/configuration](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/pc01.md): List platform configurations such as general information, modules and features activated.

Note: This configuration represents modules and major features enabled during platform setup. This differs from the PC02 API which export the platform business settings configurable by the operator in the back office.

### RE01 - List reasons

 - [GET /api/reasons](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/re01.md): This API returns cancellation, refund, incident, and message reasons.Reasons are sorted by type then sort index (set in the back-office)Call FrequencyRecommended usage: Each time a page must display a list of reasonsMaximum usage: Each time a page must display a list of reasonsRead MoreMore contextLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### SH11 - List all active shipping zones

 - [GET /api/shipping/zones](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/sh11.md): Results are sorted by index, set in the back-officeCall FrequencyRecommended usage: Once per dayMaximum usage: Once per dayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### SH12 -  List all active shipping methods

 - [GET /api/shipping/types](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/sh12.md): Results are sorted by index, set in the back-officeCall FrequencyRecommended usage: Once per dayMaximum usage: Once per dayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### SH21 - List all carriers

 - [GET /api/shipping/carriers](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/sh21.md): Results are sorted alphabetically by carrier labelCall FrequencyRecommended usage: Once per dayMaximum usage: Once per dayRead MoreMore context

### SH31 - List all logistic classes

 - [GET /api/shipping/logistic_classes](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/sh31.md): Results are sorted by index, set in the back-officeCall FrequencyRecommended usage: Once per dayMaximum usage: Once per dayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### V01 - Health Check endpoint

 - [GET /api/version](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/v01.md): Use this endpoint to check that Mirakl Platform is up.You can ignore the response body that is subject to change, checking the response code is enough.

### RE02 - List reasons by type (deprecated)

 - [GET /api/reasons/{reason_type}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/re02.md): Deprecated endpointThis API is going to be removed in future update. Consider using RE01.DescriptionThis API returns cancellation, refund, incident, and message reasons.Reasons are sorted by sort index (set in the back-office)Call FrequencyRecommended usage: Each time a page must display a list of reasonsMaximum usage: Each time a page must display a list of reasonsLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### RE11 - List of reasons with type: incident open (deprecated)

 - [GET /api/reasons/incident_open](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/re11.md): Deprecated endpointThis API is going to be removed in future update, use RE02 with parameter reason_type='INCIDENT_OPEN'DescriptionNote: Result returns only reasons where the user's role have the right Note: Reasons are sorted by sort index, set in the back-officeCall FrequencyRecommended usage: Once on incident creation page viewMaximum usage: Once on incident creation page view

### RE12 - List of reasons with type: incident close (deprecated)

 - [GET /api/reasons/incident_close](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/re12.md): Deprecated endpointThis API is going to be removed in future update, use RE02 with parameter reason_type='INCIDENT_CLOSE'DescriptionNote: Result returns only reasons where the user's role have the right Note: Reasons are sorted by sort index, set in the back-officeCall FrequencyRecommended usage: Once on incident closing page viewMaximum usage: Once on incident closing page view

### RE14 - List of reasons with type: messaging (deprecated)

 - [GET /api/reasons/messaging](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/platform-settings/re14.md): Deprecated endpointThis API is going to be removed in future update, use RE02 with parameter reason_type='MESSAGING'DescriptionNote: Result returns only reasons where the user's role have the right Note: Reasons are sorted by sort index, set in the back-officeCall FrequencyRecommended usage: Once on message creation page viewMaximum usage: Once on message creation page view

## Invoicing and Accounting

### DR11 - List accounting documents requests

 - [GET /api/document-request/requests](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/dr11.md): PaginationThis resource supports seek pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date (desc by default)

### DR12 - List of document request lines

 - [GET /api/document-request/{document_request_id}/lines](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/dr12.md): PaginationThis resource supports seek pagination (see documentation)Sort fieldssort field can have the following values:dateCreated - Sort by creation date (asc by default)

### DR73 - Download accounting documents

 - [GET /api/document-request/documents/download](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/dr73.md): At least one of the following filters must be applied: document_id or entity_idIf more than one document is requested, the output of the API will be a ZIP archive.The tree structure of this archive is as follows:
documents-1624624030618.zip
|
|__ product-logistic-order/
|   |__order1-A/|      |__ INV203837.pdf
|      |__ INV203837.cxml
|   |__order1-B/|      |__ INV203839.pdf

### DR74 - Upload accounting documents

 - [POST /api/document-request/documents/upload](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/dr74.md): Documents filenames must be distinct.If several formats are required for a document request, they must all be uploaded at once.A maximum of 50 documents can be uploaded simultaneously.

### IV01 - List accounting documents

 - [GET /api/invoices](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/iv01.md): Call FrequencyRecommended usage: Once per day and as many times as there are invoice pages returnedMaximum usage: Once per day and as many times as there are invoice pages returnedPaginationThis resource supports offset pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date (asc by default)

### IV02 - Download an accounting document

 - [GET /api/invoices/{accounting_document_id}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/iv02.md): Call FrequencyRecommended usage: At each invoice downloadMaximum usage: At each invoice download

### TL02 - List transaction lines

 - [GET /api/sellerpayment/transactions_logs](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/tl02.md): This resource uses seek pagination. The maximum allowed value for parameter limit is 2000.Call FrequencyRecommended usage: 20 times per dayMaximum usage: 20 times per min, 60 times per hourPaginationThis resource supports seek pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date (desc by default)lastUpdated - Sort by last updated date (Recommended) (desc by default)

### TL03 - Export transaction lines JSON file asynchronously

 - [POST /api/sellerpayment/transactions_logs/async](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/tl03.md): The export is asynchronous. Export status can be retrieved by calling TL04.Call FrequencyRecommended usage:  once per dayMaximum usage:  once per day

### TL04 - Poll the status of an asynchronous transaction log export (TL03)

 - [GET /api/sellerpayment/transactions_logs/async/status/{tracking_id}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/tl04.md): Retrieve the status for an TL03 transaction log export.
When the export is complete, the URLs to retrieve the files are returned.
Call FrequencyRecommended usage: Once per minute until you get an error or a successMaximum usage: Every 10 seconds

### TL05 - Retrieve transaction logs files once asynchronous transaction logs export is complete (TL04)

 - [GET /dynamic-url/The+URL+is+retrieved+from+TL04+output/TL05](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/invoicing-and-accounting/tl05.md): Retrieve each chunk of an transaction logs export file via the URL generated once the asynchronous transaction logs export is complete

## Products

### H11 - List Catalog categories (parents and children) related to a Catalog category

 - [GET /api/hierarchies](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/h11.md): Call FrequencyRecommended usage: Every hourMaximum usage: Every hourRead MoreMore context

### P31 - Get products for a list of product references

 - [GET /api/products](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/p31.md): Note: this resource returns 100 products maximum  Results are sorted by product sku asc, then by product identifier type asc and then by product identifier ascCall FrequencyRecommended usage: At each product page displayMaximum usage: At each product page displayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### P41 - Import products to the operator information system

 - [POST /api/products/imports](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/p41.md): Returns the import identifier to track the status of the importCall FrequencyRecommended usage: Every hour, for each sellerMaximum usage: Every 15 minutes, for each seller

### P51 - Get information about product import statuses

 - [GET /api/products/imports](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/p51.md): If the last_request_date param is not set the api returns all product imports.Call FrequencyRecommended usage: Every 5 minutesMaximum usage: Once per minutePaginationThis resource supports offset pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date (asc by default)

### P42 - Get the import status for a product import

 - [GET /api/products/imports/{import}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/p42.md): Call FrequencyRecommended usage: Once per minute until getting the import final statusMaximum usage: Once per minuteRead MoreMore context

### P44 - Get the error report file for a product import ("Non-integrated products report")

 - [GET /api/products/imports/{import}/error_report](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/p44.md): This API returns either a CSV file (MCM enabled) or a file in a format defined by the operator (MCM disabled).Call FrequencyRecommended usage: Each time an error report is neededMaximum usage: Each time an error report is needed

### P45 - Get the product integration report file for a product import ("Added products report")

 - [GET /api/products/imports/{import}/new_product_report](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/p45.md): This API returns either a CSV file (MCM enabled) or a file in a format defined by the operator (MCM disabled).Call FrequencyRecommended usage: Each time an integration report is neededMaximum usage: Each time an integration report is neededRead MoreMore context

### P46 - Get the transformed file for a product import ("File in operator format")

 - [GET /api/products/imports/{import}/transformed_file](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/p46.md): This API returns a CSV file.Call FrequencyRecommended usage: Each time a transformed file is availableMaximum usage: Each time a transformed file is availableRead MoreMore context

### P47 - Get the transformation error report file for a product import ("Source file error report")

 - [GET /api/products/imports/{import}/transformation_error_report](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/p47.md): This API returns a CSV, XLSX or XML file, depending on the file format provided by the seller.Call FrequencyRecommended usage: Each time an error report is neededMaximum usage: Each time an error report is neededRead MoreMore context

### PM11 - Get the product attribute configuration

 - [GET /api/products/attributes](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/pm11.md): Retrieves all attributes for parents and children of the requested hierarchyCall FrequencyRecommended usage: Every hourMaximum usage: Every hourRead MoreMore context

### VL11 - Get information about operator's value lists

 - [GET /api/values_lists](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/products/vl11.md): Call FrequencyRecommended usage: Every hourMaximum usage: Every hourRead MoreMore context

## Messages

### M10 - Retrieve a thread

 - [GET /api/inbox/threads/{thread_id}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/messages/m10.md): Call FrequencyRecommended usage: Synchronous only - At each page that includes a message thread displayMaximum usage: Synchronous only - At each page that includes a message thread display

### M11 - List all threads

 - [GET /api/inbox/threads](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/messages/m11.md): You may want to retrieve the threads linked to a specific entity, using both entity_type and entity_id.
For example, to retrieve threads for an order, use entity_type=MMP_ORDER&entity_id=my-order-1.

Available values for entity_type are:

MMP_ORDER: for threads on product orders
MMP_OFFER: for threads on offers
MPS_ORDER: for threads on service orders
MPS_SERVICE: for threads on services
SELLER_OPERATOR: for threads between sellers and operator


This resource uses seek pagination. The default value for parameter limit is 50.
Call FrequencyRecommended usage: Synchronous only - At each page that includes an inbox displayMaximum usage: Synchronous only - At each page that includes an inbox displayPaginationThis resource supports seek pagination (see documentation)

### M14 - Create a thread with the operator

 - [POST /api/inbox/threads](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/messages/m14.md): Create a thread with the operator and send a first messageCall FrequencyRecommended usage: Synchronous only - At each threadMaximum usage: Synchronous only - At each thread answer

### M12 - Reply to a thread

 - [POST /api/inbox/threads/{thread_id}/message](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/messages/m12.md): Maximum of 1000 messages on a threadCall FrequencyRecommended usage: Synchronous only - At each thread answerMaximum usage: Synchronous only - At each thread answer

### M13 - Download an attachment

 - [GET /api/inbox/threads/{attachment_id}/download](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/messages/m13.md): Call FrequencyRecommended usage: Synchronous only - At each message attachment downloadMaximum usage: Synchronous only - At each message attachment download

### OR43 - Create a thread on an order

 - [POST /api/orders/{order_id}/threads](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/messages/or43.md): Each message has a 30 Megabyte size limit, regardless of the number of attachments in the message.Call FrequencyRecommended usage: At each new thread posted on an orderMaximum usage: At each new thread posted on an order

### M01 - List messages linked to orders and offers (deprecated)

 - [GET /api/messages](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/messages/m01.md): Deprecated endpointThis API is going to be removed in a future update, please use M10 and M11 insteadDescriptionReturns messages received or sent to the shop. By default, returns only messages that are received by the shop.Call FrequencyRecommended usage: Synchronous only - at each message list displayMaximum usage: Synchronous only - at each message list displayPaginationThis resource supports offset pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date (desc by default)

### OR42 - Post a message on an order (deprecated)

 - [POST /api/orders/{order_id}/messages](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/messages/or42.md): Deprecated endpointThis API will be removed in a future version. Use OR43 and M12 instead.DescriptionMaximum of 1000 messages on a threadCall FrequencyRecommended usage: At each new message posted on an orderMaximum usage: At each new message posted on an orderRead MoreMore context

## Offers

### OF01 - Import a file to create, update or delete offers

 - [POST /api/offers/imports](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of01.md): Returns the import identifier to track the status of the import.Call FrequencyRecommended usage: Every 5 minutesMaximum usage: Once per minuteRead MoreMore context

### OF04 - Get information and statistics about offer imports

 - [GET /api/offers/imports](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of04.md): Call FrequencyRecommended usage: Every 5 minutesMaximum usage: Once per minuteRead MoreMore contextPaginationThis resource supports seek pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date (desc by default)

### OF02 - Get information and statistics about an offer import

 - [GET /api/offers/imports/{import}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of02.md): Call FrequencyRecommended usage: After each OF01 call, every 5 minutesMaximum usage: Once per minuteRead MoreMore context

### OF03 - Get the error report file for an offer import

 - [GET /api/offers/imports/{import}/error_report](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of03.md): This API returns a CSV, XLSX or XML file, depending on the file format provided by the seller.Call FrequencyRecommended usage: After each OF02 call, every 5 minutesMaximum usage: Once per minuteRead MoreMore context

### OF21 - List offers of a shop

 - [GET /api/offers](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of21.md): Call FrequencyRecommended usage: On each shop's offers page viewMaximum usage: On each shop's offers page viewRead MoreIf the "Price approval" option is activated, read this pagePrice prioritization for Advanced PricingPaginationThis resource supports offset pagination (see documentation)Sort fieldssort field can have the following values:totalPrice (Default) - Sort by total price (asc by default)price - Sort by price, total price (asc by default)productTitle - Sort by product title, total price (asc by default)LocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### OF24 - Create, update, or delete offers

 - [POST /api/offers](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of24.md): Returns the import identifier to track the status of the update.You must send all offer fields. Offer fields that are not sent are reset to their default value.Call FrequencyRecommended usage: Every 5 minutesMaximum usage: Once per minute

### OF22 - Get information about an offer

 - [GET /api/offers/{offer}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of22.md): Call FrequencyRecommended usage: At each offer page displayMaximum usage: At each offer page displayRead MoreIf the "Price approval" option is activated, read this pagePrice prioritization for Advanced PricingLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### OF52 - Export offers CSV or JSON file asynchronously

 - [POST /api/offers/export/async](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of52.md): Export status and files links can be retrieved by calling OF53.Get a CSV or JSON file that includes the offers updated and deleted since the last request date.

To ease testing processes, the minimum values for "megabytes_per_chunk" and "items_per_chunk" have been lowered on TEST and DEV environments.
Please adapt these values on PROD environments.

Call FrequencyRecommended usage: - Differential: every 5 minutes - Full: once per dayMaximum usage: - Differential: once per minute - Full: once per day

### OF53 - Poll the status of an asynchronous offer export (OF52)

 - [GET /api/offers/export/async/status/{tracking_id}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of53.md): Retrieve the status for an OF52 offer export.
When the export is complete, the URLs to retrieve the files are returned.
Call FrequencyRecommended usage: Once per minute until you get an error or a successMaximum usage: Every 10 seconds

### OF54 - Retrieve offer files once asynchronous offer export is complete (OF52)

 - [GET /dynamic-url/The+URL+is+retrieved+from+OF53+output/OF54](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of54.md): Retrieve each chunk of an offer export file via the URL generated once the asynchronous offer export is complete

### P11 - List offers for each given product

 - [GET /api/products/offers](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/p11.md): Call FrequencyRecommended usage: At each product page displayMaximum usage: At each product page displayRead MoreIf the "Price approval" option is activated, read this pagePrice prioritization for Advanced PricingAdvanced Pricing in P11PaginationThis resource supports offset pagination (see documentation)Sort fieldssort field can have the following values:bestPrice (Default) - Sorts by product sku and then by total price, premium information, shop grade (asc by default)bestEvaluation - Sorts by product sku and then by shop grade, total price, premium information (asc by default)LocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### PRI01 - Import a price file

 - [POST /api/offers/pricing/imports](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/pri01.md): Import a .csv file to submit all applicable prices for an offer.
The import mode is delete and replace: any existing price that is not submitted will be deleted.
If Price Approval is enabled, this API creates and updates pending prices; ongoing prices will remain.
Returns an import identifier to track the status of the import and retrieve an error report if applicable.
Call FrequencyRecommended usage: Every 5 minutesMaximum usage: Once per minuteRead MoreImporting pricesAbout the price file format

### PRI02 - Get information and statistics about an offer pricing import

 - [GET /api/offers/pricing/imports](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/pri02.md): Call FrequencyRecommended usage: After each PRI01 call, every 5 minutesMaximum usage: Once per minuteRead MoreImporting pricesPaginationThis resource supports seek pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date (desc by default)

### PRI03 - Get the error report for a price import in CSV format

 - [GET /api/offers/pricing/imports/{import_id}/error_report](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/pri03.md): Only returns lines of offers with at least one offer price in error.
The first column contains the line number in error. The second column contains the error reason.
The returned file is ready to be reimported after the values have been fixed.
Offer prices that were submitted in the price import but don't appear in the error report were successfully imported.
Call FrequencyRecommended usage: After each PRI02 call, every 5 minutesMaximum usage: Once per minuteRead MoreImporting prices

### STO01 - Import a stock file

 - [POST /api/offers/stock/imports](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/sto01.md): Import a .csv file to update stock for offers, either globally or per warehouse.
Returns an import identifier to track the status of the import and retrieve an error report if applicable.
Call FrequencyRecommended usage: Every 5 minutes when stock needs updatingMaximum usage: Once per minuteRead MoreMore contextAbout the stock import file format

### STO02 - Get information and statistics about an offer stock import

 - [GET /api/offers/stock/imports/{import_id}/status](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/sto02.md): Call FrequencyRecommended usage: After each STO01 call, every 5 minutesMaximum usage: Once every 15 secondsRead MoreMore context

### STO03 - Get the error report for a stock import in CSV format

 - [GET /api/offers/stock/imports/{import_id}/error_report](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/sto03.md): Only returns lines of offers with at least one offer price in error.
The first column contains the line number in error. The second column contains the error reason.
The returned file is ready to be reimported after the values have been fixed.
Offer prices that were submitted in the price import but don't appear in the error report were successfully imported.
Call FrequencyRecommended usage: After each STO02 call, every 5 minutesMaximum usage: Once per minuteRead MoreMore context

### OF26 - Get the quantity of stock available for an offer. (deprecated)

 - [GET /api/offers/{offer}/quantity](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of26.md): Quantity return rules: 0: if quantity = 0 or the offer is not available x: quantity available

### OF51 - Get offers CSV file (deprecated)

 - [GET /api/offers/export](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/offers/of51.md): Deprecated endpointThis API is going to be removed in a future update, please use APIs OF52, OF53, and OF54 instead.DescriptionGet a CSV file that includes the offers updated and deleted since the last request date.For deleted offers, only offer-id, product-sku, shop-id, shop-sku, active and deleted columns are returned. If the last_request_date param is not set the api returns all the active offers (inactive offers can be included with include_inactive_offers parameter).If offers have custom fields, a column is added for each existing custom field with as header the code of the custom field.Results are sorted by offer identifier.Call FrequencyRecommended usage: - Differential: every 5 minutes - Full: once per dayMaximum usage: - Differential: once per minute - Full: once per day

## Orders

### OR04 - Patch update orders

 - [PUT /api/orders](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or04.md): Update orders information field by field: unspecified fields will not be updated. To remove the value for a field, send it with the 'null' value (not allowed for the required fields).You cannot use API OR04 to update customer-related information if the customer has been anonymized via API AN01.A maximum of 100 orders can be sent at once.Call FrequencyRecommended usage: At each information update of one or multiple orders (for example: to modify the billing address)Maximum usage: Once per minute, 100 orders per callRead MoreMore context

### OR11 - List orders with pagination

 - [GET /api/orders](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or11.md): Pagination is enabled by default. For large requests, use asynchronous order export APIs OR13, OR14 and OR15 instead.Call FrequencyRecommended usage: - Asynchronous: every 5 minutes - Synchronous: at each order page displayMaximum usage: - Asynchronous: once per minute - Synchronous: at each order page displayPaginationThis resource supports offset pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date, and then by order identifier (asc by default)LocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### OR07 - Update order line shipping origin

 - [PUT /api/orders/shipping_from](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or07.md): Update shipping origin (shipping_from) information on order lines. A maximum of 100 order lines can be sent at once.Call FrequencyRecommended usage: At each update of shipping origin on one or multiple order linesMaximum usage: 60 per hour, 100 order lines per call

### OR13 - Export orders asynchronously

 - [POST /api/orders/async-export](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or13.md): The API returns a tracking id to be used to query API OR14.Mirakl recommends to use API OR13 instead of API OR11 as it can handle very large volumes of data.You must give at least one date range filter: created or last updated date.API OR13 supports the chunk of the export file into multiple files in order to:respect a maximum megabyte weight using the megabytes_per_chunk parameter.respect a maximum amount of exported items using the items_per_chunk parameter.Only one export request can be created for the same shop account.Call FrequencyRecommended usage: - Differential: every 15 minutesMaximum usage: - Differential: every 5 minutes - Full: every 24 hoursLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### OR14 - Get the status of an asynchronous order export.

 - [GET /api/orders/async-export/status/{tracking_id}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or14.md): Use this API to query the order export status after an API OR13 call.Until the export via API OR13 is complete, the status returned by API OR14 is PENDING.You must call API OR14 until you get the COMPLETED status which correspond to a completed and successful export from API OR13.The URLs in API OR14 response contain all the files from API OR13 export.Browse those urls and query them using the GET method.In case of error, the status is FAILED.In case of export canceled, the status is CANCELED.

### OR15 - Retrieve order export files once asynchronous export is complete (OR13).

 - [GET /dynamic-url/The+URL+is+retrieved+from+OR14+output/OR15](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or15.md): Retrieve each chunk of an order export file via the URL generated once the asynchronous export is complete.

### OR21 - Accept or refuse order lines

 - [PUT /api/orders/{order_id}/accept](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or21.md): Accept or refuse order lines in the WAITING_ACCEPTANCE statusCall FrequencyRecommended usage: At each new order on the MarketplaceMaximum usage: At each new order on the MarketplaceRead MoreMore context

### OR23 - Update carrier tracking information for a specific order

 - [PUT /api/orders/{order_id}/tracking](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or23.md): If the carrier is not registered, the complete tracking url can be provided.Call FrequencyRecommended usage: At each order tracking information update (as soon as the seller gets the tracking number from the carrier)Maximum usage: At each order tracking information update (as soon as the seller gets the tracking number from the carrier)

### OR24 - Validate the shipment of an order

 - [PUT /api/orders/{order_id}/ship](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or24.md): Validate the shipment of an order in the SHIPPING statusCall FrequencyRecommended usage: Each time the tracking number is entered (OR23)Maximum usage: Each time the tracking number is entered (OR23)

### OR28 - Perform refunds on order lines

 - [PUT /api/orders/refund](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or28.md): Call FrequencyRecommended usage: At each refund requestMaximum usage: At each refund request

### OR29 - Perform a full cancelation of an order

 - [PUT /api/orders/{order_id}/cancel](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or29.md): Call FrequencyRecommended usage: At each order cancelationMaximum usage: At each order cancelation

### OR30 - Perform cancelations on order lines

 - [PUT /api/orders/cancel](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or30.md): Call FrequencyRecommended usage: At each order (or order line) cancelationMaximum usage: At each order (or order line) cancelation

### OR31 - Update the custom fields of an order and its order lines

 - [PUT /api/orders/{order_id}/additional_fields](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or31.md): Only specified custom field values will be updated.In order to delete an custom field's value, set it to null or an empty string. Note that you may not delete the value of a required custom field value.Output will return information on the status of the update attempt by giving:    either all of the order and its order lines custom field values after the update    or in case of errors, the list of errors and the body of the initial callCall FrequencyRecommended usage: Each time a custom field is updated on an order or on an order lineMaximum usage: Each time a custom field is updated on an order or on an order line

### OR32 - Adjust order line

 - [PUT /api/orders/adjust](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or32.md): Update order line actual measurement either upwards or downwards, within the limit defined at the platform level.Call FrequencyRecommended usage: At each adjustment of one or multiple order linesMaximum usage: Once per minute, 100 order lines per call

### OR51 - Get the evaluation of an order

 - [GET /api/orders/{order_id}/evaluation](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or51.md): Call FrequencyRecommended usage: On each evaluation page viewMaximum usage: On each evaluation page viewLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### OR72 - Lists order's documents

 - [GET /api/orders/documents](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or72.md): Returns a list of all the documents available on the orderCall FrequencyRecommended usage: At each document list page displayMaximum usage: At each document list page display

### OR73 - Download one or multiple documents attached to one or multiple orders

 - [GET /api/orders/documents/download](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or73.md): If a list of document identifiers is specified only these documents are downloaded.                  If more than one document id is specified, the documents will be wrapped in a ZIP archive           If only one document id is specified the document will not be zipped             If a list of order identifiers is specified, all documents from those orders are downloaded.   Use a list of order document type codes to retrieve specific types from those orders.   In this case, the output of the API will always be a ZIP archive even if there is only one document to retrieve.   When documents are retrieved, they're wrapped into a ZIP archive except when only one document id is specified. The tree structure of this archive is as follow:
documents-timestamp.zip
|
|__ order_id_x/
|   |__ foo.txt
|   |__ bar.txt
|   |__ baz.pdf
|
|__ order_id_y/
|   |__ image.png
|   |__ image(1).png
Call FrequencyRecommended usage: At each document downloadMaximum usage: At each document download

### OR74 - Upload documents to attach to an order

 - [POST /api/orders/{order_id}/documents](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or74.md): Documents filenames must be distinct. Only documents of the following types are supported: csv, doc, xls, xlsx, ppt, pdf, odt, ods, odp, txt, rtf, png, jpg, gif, zpl, mov, mp4.
An order can have a maximum of 50 documents.
    In the API output we include only documents with errors. All other documents are successfully uploaded.

For system document types, there are specific restrictions :

    SYSTEM_DELIVERY_BILL/SYSTEM_SHIPMENT_DELIVERY_BILL : restricted to operator role.
    SYSTEM_MESSAGE_ATTACHMENT : cannot be directly uploaded to an order.

Call FrequencyRecommended usage: At each document upload on an orderMaximum usage: At each document upload on an order

### OR75 - List all the order taxes available on the platform

 - [GET /api/orders/taxes](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or75.md): Call FrequencyRecommended usage: Once per dayMaximum usage: Once per dayLocalizationThis resource supports locale parameter (see documentation)Localized output fields will be highlighted with an icon:

### OR76 - Delete an order document

 - [DELETE /api/orders/documents/{document_id}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or76.md): Call FrequencyRecommended usage: At each order document deletionMaximum usage: At each order document deletion

### OR12 - Get information about an order (deprecated)

 - [GET /api/orders/{order_id}](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or12.md): Deprecated endpointThis API is going to be removed in a future update, please use OR11 with the query parameter 'order_ids' instead.DescriptionCall FrequencyRecommended usage: On each order page viewMaximum usage: On each order page view

### OR26 - Perform a refund of order lines of an order (deprecated)

 - [PUT /api/orders/{order_id}/refund](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or26.md): Deprecated endpointThis API is going to be removed in a future update, please use OR28 instead.DescriptionCall FrequencyRecommended usage: On each new refund demandMaximum usage: On each new refund demand

### OR41 - List messages of an order (deprecated)

 - [GET /api/orders/{order_id}/messages](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/orders/or41.md): Deprecated endpointThis API is going to be removed in a future update, please use M10 and M11 insteadDescriptionBy default, all sent, received and unarchived message are listedCall FrequencyRecommended usage: On each message page viewMaximum usage: On each message page viewPaginationThis resource supports offset pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date (desc by default)

## Incidents

### OR64 - Mark an incident as resolved

 - [PUT /api/orders/{order_id}/lines/{line}/resolve_incident](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/incidents/or64.md): Call FrequencyRecommended usage: At each incident resolution on an order lineMaximum usage: At each incident resolution on an order lineRead MoreMore context

## Picklists

### PL11 - List picklists

 - [GET /api/picklists](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/picklists/pl11.md): Call FrequencyRecommended usage: Every 15 minutesMaximum usage: Every 5 minutesPaginationThis resource supports seek pagination (see documentation)Sort fieldssort field can have the following values:pickupDate (Default) - Sort by pickup date (asc by default)

## Promotions

### PR01 - List promotions

 - [GET /api/promotions](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/promotions/pr01.md): Call FrequencyRecommended usage: At each display of a promotions list page or on-promo offer detail page.Maximum usage: At each display of a promotions list page or on-promo offer detail page.PaginationThis resource supports offset pagination (see documentation)Sort fieldssort field can have the following values:startDate (Default) - Sort by promotion activity start date (Newest first) (desc by default)endDate - Sort by promotion activity end date (Newest first) (desc by default)dateCreated - Sort by promotion creation date (Newest first) (desc by default)

## Users

### RO02 - List shop roles

 - [GET /api/users/shops/roles](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/users/ro02.md): Call FrequencyRecommended usage: On each user role viewMaximum usage: On each user role viewRead MoreMore context

## Returns

### RT04 - Patch update returns

 - [PUT /api/returns](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/returns/rt04.md)

### RT11 - List returns

 - [GET /api/returns](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/returns/rt11.md): Call FrequencyRecommended usage: Every 15 minutesMaximum usage: Every 5 minutesPaginationThis resource supports seek pagination (see documentation)Sort fieldssort field can have the following values:date_created (Default) - Sort by return date creation (asc by default)

### RT21 - Accept or refuse a return request

 - [PUT /api/returns/accept](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/returns/rt21.md): Limited to 100 returns at a timeRead MoreMore context

### RT25 - Validate returns as received

 - [PUT /api/returns/receive](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/returns/rt25.md): Limited to 100 returns at a time

### RT26 - Mark a return as compliant or non compliant

 - [PUT /api/returns/compliance](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/returns/rt26.md): Limited to 100 returns at a time

### RT27 - Mark a return as closed

 - [PUT /api/returns/close](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/returns/rt27.md): Limited to 100 returns at a time

### RT29 - Mark a return as canceled

 - [PUT /api/returns/cancel](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/returns/rt29.md): Limited to 100 returns at a time

## Multiple shipments

### ST01 - Create shipments

 - [POST /api/shipments](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/multiple-shipments/st01.md): Limited to 1000 shipments at a timeCall FrequencyRecommended usage: On each new shipmentMaximum usage: On each new shipment

### ST07 - Update shipment shipping origin

 - [PUT /api/shipments](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/multiple-shipments/st07.md): Limited to 100 shipments at a timeCall FrequencyRecommended usage: At each update of shipments for one or multiple shipment

### ST11 - List shipments

 - [GET /api/shipments](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/multiple-shipments/st11.md): Call FrequencyRecommended usage: at each shipment page displayMaximum usage: at each shipment page displayPaginationThis resource supports seek pagination (see documentation)Sort fieldssort field can have the following values:dateCreated (Default) - Sort by creation date (asc by default)

### ST06 - Delete shipments

 - [PUT /api/shipments/delete](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/multiple-shipments/st06.md): Limited to 1000 shipments at a timeCall FrequencyRecommended usage: On each shipment deletionMaximum usage: On each shipment deletion

### ST12 - List items to ship

 - [GET /api/shipments/items_to_ship](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/multiple-shipments/st12.md): Call FrequencyRecommended usage: Every 15 minutesMaximum usage: Every 5 minutesPaginationThis resource supports seek pagination (see documentation)Sort fieldssort field can have the following values:shippingDate (Default) - Sort by shipping date (asc by default)

### ST23 - Update carrier tracking information for shipments

 - [POST /api/shipments/tracking](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/multiple-shipments/st23.md): If the carrier is not registered, the complete tracking url can be provided. Limited to 1000 shipments at a time.Call FrequencyRecommended usage: On each shipment tracking info updateMaximum usage: On each shipment tracking info update

### ST24 - Validate shipments as shipped

 - [PUT /api/shipments/ship](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/multiple-shipments/st24.md): Limited to 1000 shipments at a timeCall FrequencyRecommended usage: On each shipment shippingMaximum usage: On each shipment shipping

### ST26 - Validate shipments as ready to pick up

 - [PUT /api/shipments/ready_for_pick_up](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/multiple-shipments/st26.md): Limited to 1000 shipments at a timeCall FrequencyRecommended usage: On each shipment ready to pick upMaximum usage: On each shipment ready to pick up

### ST31 - Update shipment additional information

 - [PUT /api/shipments/additional_information](https://developer.mirakl.com/content/product/mmp/rest/seller/openapi3/multiple-shipments/st31.md): Limited to 100 shipments at a timeCall FrequencyRecommended usage: At each update of shipments for one or multiple shipments
