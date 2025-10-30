# REMIT Data - Unplanned Unavailability of Electrical Facilities

## Overview

REMIT (Regulation on Wholesale Energy Market Integrity and Transparency) is a European Union regulation designed to increase transparency in wholesale energy markets. One of the key data feeds provided through REMIT is information about the unavailability of electrical facilities, both planned and unplanned.

Our system now collects REMIT data through the Elexon IRIS (Insights Real-time Information Service) client, which provides real-time notifications of changes to electricity generation and transmission availability.

## Data Structure

The REMIT data for unplanned unavailability of electrical facilities contains detailed information about outages and capacity reductions at power plants and other electrical infrastructure. Each REMIT message typically includes:

### Key Fields

| Field                 | Description                                                            |
| --------------------- | ---------------------------------------------------------------------- |
| `publishTime`         | When the message was published by Elexon                               |
| `mrid`                | Message Reference ID - unique identifier for the message               |
| `revisionNumber`      | Version of the message (increments with updates)                       |
| `messageType`         | Type of message (e.g., "UnavailabilitiesOfElectricityFacilities")      |
| `messageHeading`      | Summary heading (e.g., "Actual Availability of Generation Unit")       |
| `eventType`           | Category of event (e.g., "Production unavailability")                  |
| `unavailabilityType`  | Whether the outage is "Planned" or "Unplanned"                         |
| `participantId`       | ID of the market participant reporting the outage                      |
| `assetId`             | Identifier for the affected asset                                      |
| `assetType`           | Type of asset (e.g., "Production", "Transmission")                     |
| `affectedUnit`        | Name of the affected unit                                              |
| `affectedUnitEIC`     | Energy Identification Code for the affected unit                       |
| `biddingZone`         | Market bidding zone (e.g., "10YGB----------A" for Great Britain)       |
| `fuelType`            | Type of fuel used by the generation unit                               |
| `normalCapacity`      | Normal operating capacity in MW                                        |
| `availableCapacity`   | Available capacity during the event in MW                              |
| `unavailableCapacity` | Capacity unavailable during the event in MW                            |
| `eventStatus`         | Status of the event (e.g., "Active", "Cancelled", "Inactive")          |
| `eventStartTime`      | Start time of the unavailability                                       |
| `eventEndTime`        | Expected end time of the unavailability                                |
| `cause`               | Reason for the unavailability (e.g., "Turbine / Generator")            |
| `relatedInformation`  | Additional details about the event                                     |
| `outageProfile`       | Array of time periods with different capacity levels during the outage |

### Outage Profile Structure

The `outageProfile` is an array of objects, each containing:
- `startTime`: Beginning of a period
- `endTime`: End of a period
- `capacity`: Available capacity during this period in MW

## Data Flow

1. **Collection**: The Elexon IRIS client receives REMIT messages in real-time as they are published
2. **Storage**: Messages are saved as JSON files in the `/Users/georgemajor/jibber-jabber 24 august 2025 big bop/elexon_iris/data/REMIT/` directory
3. **Processing**: Every 5 minutes, the `iris_to_bigquery.py` script processes new files
4. **Archiving**: Files older than 1 hour are moved to the `/Users/georgemajor/jibber-jabber 24 august 2025 big bop/elexon_iris/processed/REMIT/` directory

## Significance of Unplanned Unavailability Data

Unplanned unavailability data is particularly valuable for:

1. **Market Analysis**: Sudden outages can cause significant price movements in energy markets
2. **System Balancing**: National Grid ESO uses this information to manage system balance
3. **Trading Strategies**: Energy traders can adjust positions based on unexpected capacity changes
4. **Forecasting**: Improved input for short-term price and demand forecasts
5. **Risk Management**: Better assessment of system reliability and potential supply shortfalls

## Example Data

Here's an example of a REMIT message for an unplanned unavailability:

```json
{
  "publishTime": "2025-09-17T14:26:47Z",
  "mrid": "11XINNOGY------2-NGET-RMT-00207306",
  "revisionNumber": 4,
  "createdTime": "2025-09-17T14:25:36Z",
  "messageType": "UnavailabilitiesOfElectricityFacilities",
  "messageHeading": "Actual Availability of Generation Unit",
  "eventType": "Production unavailability",
  "unavailabilityType": "Unplanned",
  "participantId": "INNOGY01",
  "registrationCode": "11XINNOGY------2",
  "assetId": "T_STAY-3",
  "assetType": "Production",
  "affectedUnit": "STAY-3",
  "affectedUnitEIC": "48W000000STAY-3U",
  "biddingZone": "10YGB----------A",
  "fuelType": "Fossil Gas",
  "normalCapacity": 457,
  "availableCapacity": 0,
  "unavailableCapacity": 413,
  "eventStatus": "Active",
  "eventStartTime": "2025-09-17T07:37:38Z",
  "eventEndTime": "2025-09-17T22:01:00Z",
  "cause": "Turbine / Generator",
  "relatedInformation": "Estimated End Date / Time changed to 17 Sep 2025 22:01 (GMT); Detailed MEL profile has changed",
  "dataset": "REMIT",
  "outageProfile": [
    {
      "startTime": "2025-09-17T07:37:38.000Z",
      "endTime": "2025-09-17T07:37:38.000Z",
      "capacity": 413
    },
    {
      "startTime": "2025-09-17T07:37:38.000Z",
      "endTime": "2025-09-17T07:54:05.000Z",
      "capacity": 125
    },
    {
      "startTime": "2025-09-17T07:54:05.000Z",
      "endTime": "2025-09-17T07:56:05.000Z",
      "capacity": 43
    },
    {
      "startTime": "2025-09-17T07:56:05.000Z",
      "endTime": "2025-09-17T08:00:00.000Z",
      "capacity": 0
    },
    {
      "startTime": "2025-09-17T08:00:00.000Z",
      "endTime": "2025-09-17T22:00:00.000Z",
      "capacity": 0
    },
    {
      "startTime": "2025-09-17T22:00:00.000Z",
      "endTime": "2025-09-17T22:01:00.000Z",
      "capacity": 408
    }
  ]
}
```

## Analysis Opportunities

The REMIT data on unplanned unavailability presents numerous analytical opportunities:

1. **Impact Analysis**: Correlate unplanned outages with market price movements
2. **Reliability Metrics**: Calculate average outage durations by plant type, fuel type, or operator
3. **Seasonal Patterns**: Identify seasonal trends in unplanned outages
4. **Cascade Effects**: Detect patterns where one outage leads to others
5. **Forecasting Models**: Develop probabilistic models of unplanned outages for risk assessment

## Data Volume and Update Frequency

- **Message Volume**: Typically 50-200 REMIT messages per day
- **Update Frequency**: Real-time as events occur
- **Size**: Each message is approximately 1-5 KB

## BigQuery Integration

The REMIT data is being collected for loading into BigQuery. The recommended schema for the REMIT table would include all fields from the JSON structure, with nested fields for the outage profile.

## Access and Visualization

This data can be accessed and visualized through:

1. **Direct Query**: SQL queries against the BigQuery dataset
2. **Dashboard Tools**: Connect Power BI, Tableau, or other visualization tools to the BigQuery dataset
3. **Raw Data**: Access the JSON files directly from the storage directory
4. **API Integration**: Build custom applications to query and display the data

## Conclusion

The REMIT data on unplanned unavailability of electrical facilities provides critical insights into the operation and reliability of the UK electricity system. By collecting and analyzing this data, we can better understand market dynamics, improve forecasting models, and identify reliability issues in the power grid.
