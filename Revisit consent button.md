Revisit consent button







Skip to main content
 Home
header search

Data Portal
Data Portal
User account menu
Main navigation
What we do
What we do
Solar panels in field
We bring together eight activities required to deliver the plans, markets and operations of the energy system of today and the future. Bringing these activities together in one organisation encourages holistic thinking on the most cost-efficient and sustainable solutions to the needs of our customers.

 View
Strategic Planning
Security of Supply
Systems Operations
Connections Explained
Resilience & Emergency Management
Energy Insights
Energy Markets
Data & AI
Helping our customers get ready for NESO
Energy 101
Energy 101
Smiling lady working at laptop
We’re experts in all things energy – how much we use, where it comes from and how it moves around Great Britain. And we want to share all that knowledge with you.

 View
Net zero explained
Great Britain’s Monthly Energy Stats
Electricity explained
Hydrogen explained
Gas explained
Balancing the Grid - Interactive game
Industry information
Industry information
Wind turbine in the sea
Are you a balancing provider looking to supply services to us, trying to find the latest Grid Code, or TNUoS charging guidance? Find all the information you need including our operational data, forecasts, and reports designed to help you make efficient decisions.

 View
Balancing costs
Balancing services
Charging
Codes
Connections
Connections Reform
Flexibility
Market Monitoring
Industry data and reports
Network access planning
Reformed National Pricing
System Access Reform
News and events
News and events
All the latest news from the heart of Great Britain's electricity system. Find out how we balance the grid, how we’re innovating for the future, and who the people are that are working on Britain's energy system around the clock.

 View
Publications
Publications
Man doing woodwork in his workshop
We've got a wide range of publications offering energy insights and analysis. Download our reports and data to see the innovative ways we are transforming the future of Great Britain’s energy.

 View
View all of our publications
Beyond 2030
Future Energy Scenarios (FES)
Transitional Centralised Strategic Network Plan (tCSNP)
Clean Power 2030
Electricity Ten Year Statement (ETYS)
GB 36 Bus electricity transmission network model
North Hyde Review
Markets Roadmap
Summer Outlook
Winter Outlook
Whole electricity system
System Operability Framework (SOF)
Regional Development Programmes
Careers
Careers
 View
About
About
Dad and son working on kitchen table
We ensure that Great Britain has the essential energy it needs by making sure supply meets demand every second of every day.

 View
Strategic priorities
Our people
A whole system challenge
Operational information
Innovation
Our progress towards net zero
Our projects
Help us improve
Your insights help us grow and improve, whether it’s a suggestion, a concern, or a bright idea, we’d love to hear it.
What could we do to make things even better for you? Tell us here

Show favourites
Help
Breadcrumb
Home
…
API Guidance

Add to favourites
API guidance

Introduction

This page provides further details on the Data Portal’s application programming interface (API), for users who wish to write code to access information from the Data Portal site (rather than downloading through the user interface).

The intention of this guide is to provide an overview of the functionality and not to serve as a tutorial for using an API. To fully utilise the API functionality, general programming skills and knowledge of SQL are needed.

The guidelines for using API

In a continued effort to enhance customer experience, we are not only conducting maintenance to address your API-related queries we strongly suggest using the below guidelines to make your use of the data portal API efficient. If the data consumer is not following the best practise for using the API and therefore overloading the server which causes performance issues then we reserve the right to block that IP address.

The rate limits are as follows:

CKAN API:  It is recommended to limit requests to a maximum one request per second.
Datastore API:  The Datastore API is designed to query and retrieve data records from datasets. While it's a powerful feature, querying large datasets can be resource-intensive. Therefore, to ensure that the server's resources are not excessively strained, we recommend limiting requests to a maximum of two requests per minute.
Here are some guidelines for efficient data retrieval:

1: Avoid frequent data fetching
If you are fetching data frequently to check whether it has changed, it is recommended to use the resource_show endpoint to obtain information about the resource modification date.
 /resource_show?id=<resource_id>

By comparing the modification date of the resource, you can determine whether you need to fetch updated data and use Datastore API to fetch the resource if you need to.

2: Utilize the Datastore API
If you need to consume data records from a CKAN resource, consider using the Datastore API for efficient retrieval and filtering of data.

e.g. using datastore_search  API
/datastore_search?resource_id=resource_id&filters={"column_name": "filter_value"}

e.g. using datastore_search_sql API
/datastore_search_sql?SELECT * FROM “<resource_id>” WHERE “column_name” = ‘filter_value’

This approach allows you to query and retrieve specific data records based on filters, minimizing the data transfer and processing overhead.


List of supported API calls

The URL for the calls is: https://api.neso.energy/api/3/action/

It is worth noting that the naming conventions in the API differ from those in the Data Portal, the table below shows how the terms relate:

API 	Data Portal
Organization 	Data Group
Package 	Dataset
Resource 	Data File
The Data Portal has been built using the CKAN platform, the following subset of CKAN endpoints are supported on the Data Portal:

End Point	Example	Description
organization_list 	https://api.neso.energy/api/3/action/organization_list 	Displays list of Data Groups on the Data Portal
package_list  	https://api.neso.energy/api/3/action/package_list  	Display list of datasets on the Data Portal
tag_list  	https://api.neso.energy/api/3/action/tag_list 	Display a list of tags on the Data Portal
package_search?q={query}  	https://api.neso.energy/api/3/action/package_search?q=BSUOS 	Displays datasets matching a criteria
resource_search?q={query}  	https://api.neso.energy/api/3/action/resource_search?query=name:BSUOS 	Displays data files matching a criteria
resource_show?q={query}	https://api.neso.energy/api/3/action/resource_show?id=8da765a1-004f-46a5-8b3f-0e5b1787fcb1 	Displays the metadata of a resource.
package_show?id={dataset_id}  	https://api.neso.energy/api/3/action/package_show?id=embedded-wind-and-solar-forecasts 	Displays dataset details
datastore_search 	https://api.neso.energy/api/3/action/datastore_search?resource_id=db6c038f-98af-4570-ab60-24d71ebd0ae5&limit=5
Parameters here 	Displays search data in a tabular file
datastore_search_sql?sql={sql}  	Parameters here  	Search data in a tabular file with SQL:  Examples are provided in the section below.


Querying data via SQL

The datastore_search_sql action allows a user to search data in a resource or connect multiple resources with join expressions. The underlying SQL engine is the PostgreSQL engine.

Example:

/datastore_search_sql? sql=SELECT”field id” FROM “resource id”

Field ID

Field IDs must be in double quotes and can be found by previewing the table view on the explore section of any resource.

For example:

Image
Field IDs


Resource ID

The resource ID can be obtained by accessing the “API” button from any resource page and will be in the “Querying” section under the “Query example (via SQL statement)” or from the bottom of the dataset page under “Integrate this dataset using cURL” section. The resource ID must also be represented in double quotes.

Image
Resource ID
Examples:

Example 	End Point 	Description
Return records matching field value	https://api.neso.energy/api/3/action/datastore_search_sql?sql=select "Date" from "b98095a8-310a-4fee-8d51-e20531c49465" WHERE "Date" >= '2022-04-01' AND "Date" <= '2022-04-02' LIMIT 500	The resource ID “aec5601a-7f3e-4c4c-bf56-d8e4184d3c5b” is the day ahead demand forecast data file, and the results are being filtered by cardinal point “1B” which is the lowest demand of the day.
Return an aggregated value based on search parameters	https://api.neso.energy/api/3/action/datastore_search_sql?sql=SELECT SUM("Constraints") from "7bcd8e25-c148-4cdb-b46f-394f88b92db5" WHERE "SETT_PERIOD" BETWEEN '7' AND '14' AND "SETT_DATE" = '2020-04-01T00:00:00'	This query returns the constraints spend for EFA block 2 on 01/04/2020 from the resource ID “7bcd8e25-c148-4cdb-b46f-394f88b92db5” which is the daily costs table 2019-2020.
For any queries or feedback please contact  opendata@neso.energy
Footer
About NESO
Who we are
Operational information
Careers
Applications, portals and APIs
Contact us
How to report a power cut
Help centre
Media centre
Corporate information
Suppliers
Freedom of Information and Environmental Information Regulations
Modern Slavery Statement
Public Sector Equality Duty (PSED)
Site
Accessibility
Privacy notice
Cookie policy
Terms and Conditions
Security
Responsible Disclosure
Social
 Twitter
 LinkedIn
 YouTube

