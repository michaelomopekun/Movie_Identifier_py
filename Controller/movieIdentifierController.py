from Service.TrailerSearchService import TrailerSearchService

search_service = TrailerSearchService()

results = search_service.search("Paul Atreides_Feyd-Rautha.mp4", top_k=3)

for match in results:

    with open("logs/search_result_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"ID: {match['id']}\n")
        log_file.write(f"Document: {match['document']}\n")
        log_file.write(f"Metadata: {match['metadata']}\n")
        log_file.write(f"Distance: {match['distance']}\n")
        log_file.write("-" * 50 + "\n")

