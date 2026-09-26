// A fictional operations SOP for trying the app without a real document.
export const SAMPLE_DOCUMENT = {
  name: 'Brightline Fulfillment — Operations SOP (sample)',
  text: `BRIGHTLINE FULFILLMENT CO. — OPERATIONS STANDARD OPERATING PROCEDURES (INTERNAL)

1. Company overview
Brightline Fulfillment is a third-party logistics provider based in Columbus, Ohio. We store, pick, pack and deliver products for 180 small and mid-sized online retailers from two warehouses (62,000 sq ft total) and run a fleet of 24 delivery vans for same-day and next-day delivery within 120 miles. Revenue comes from monthly storage fees, a per-order fulfilment fee and delivery charges. We ship roughly 4,500 orders per day, peaking at 9,000 in November and December. Headcount: 140 warehouse staff, 26 drivers, 6 dispatchers, 4 procurement staff, 5 customer-service agents and a 3-person finance team.

2. Systems in use
- Orders arrive from Shopify and WooCommerce stores and are exported to CSV twice a day.
- Inventory is tracked in a legacy on-premise WMS (2012) with no API; stock counts are also kept in shared Excel workbooks.
- Dispatch planning is done in Excel with Google Maps open in a browser tab.
- Drivers receive their routes as screenshots in WhatsApp groups.
- Finance uses QuickBooks Online. Customer service works from a shared Gmail inbox.

3. Process A: Order intake
Twice a day a coordinator downloads the CSV exports from each store platform, cleans the columns, and re-keys them into the WMS import template. This takes about 2.5 hours per day. Around 1.5% of orders have address or SKU errors that are only discovered at packing.

4. Process B: Driver route dispatching
Every morning, 3 dispatchers spend 2 to 3 hours building delivery routes for 24 vans by hand. They sort addresses by postcode in Excel, check traffic in Google Maps and paste the stop list into WhatsApp. Routes are rarely optimal; our average van runs 18% more miles than the planned distance, and late-afternoon re-routing for failed deliveries is done by phone.

5. Process C: Replenishment and purchase orders
When a client's SKU falls below its reorder point, the warehouse lead notices it in the Excel stock sheet (checked manually each afternoon) and messages the Procurement Director on Slack. The Director drafts a PDF purchase order in Word, emails it to the supplier and logs it in a tracking spreadsheet. The procurement team spends about 14 hours per week on this. Stock-outs caused 310 late orders last quarter, and we regularly promote items on client websites that we don't actually have in stock.

6. Process D: Delivery status requests
Customer service receives around 350 "where is my order?" emails per day. Agents look up the order in the WMS, ask the driver on WhatsApp, and reply by email. Each request takes 4 to 6 minutes; the team spends roughly 30 hours per week on these enquiries and response times exceed 24 hours during peak season.

7. Process E: Month-end billing
Finance builds each client's monthly invoice by combining storage data from the WMS, order counts from the store exports and delivery logs from WhatsApp screenshots. Billing takes 3 people about 5 working days each month. Roughly 1 in 12 invoices is disputed because of counting errors.

8. Goals for next year
Leadership wants to grow to 250 clients without adding dispatch, procurement or finance headcount, cut late deliveries by half, and give clients a live view of their stock and orders.`,
}
