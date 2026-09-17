from app.clients.openalex import OpenAlexClient

client = OpenAlexClient()

work = client.get_work("W2741809807")

print(work["id"])
print(work["display_name"])
print(work["publication_year"])
print(work["cited_by_count"])