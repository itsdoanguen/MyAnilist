import requests
import json

url = "https://graphql.anilist.co"

# Query để lấy thông tin nextAiringEpisode và airingSchedule của anime theo ID
query = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    format
    status
    episodes
    nextAiringEpisode {
      id
      airingAt
      timeUntilAiring
      episode
    }
    airingSchedule {
      nodes {
        id
        airingAt
        timeUntilAiring
        episode
      }
      pageInfo {
        total
        perPage
        currentPage
        lastPage
        hasNextPage
      }
    }
  }
}
"""

# Thay đổi ID này để test với anime khác
anime_id = 21  # One Piece (anime đang airing)

variables = {
    "id": anime_id
}

print(f"🔍 Đang lấy thông tin airingSchedule cho anime ID: {anime_id}...\n")

try:
    resp = requests.post(url, json={"query": query, "variables": variables}, timeout=10)
    data = resp.json()
    
    if "errors" in data:
        print("❌ Lỗi từ API:")
        print(json.dumps(data["errors"], indent=2, ensure_ascii=False))
    else:
        media = data.get("data", {}).get("Media", {})
        
        if not media:
            print(f"❌ Không tìm thấy anime với ID: {anime_id}")
        else:
            title = media.get("title", {})
            print(f"📺 Anime: {title.get('romaji', 'N/A')}")
            print(f"   ID: {media.get('id')}")
            print(f"   Format: {media.get('format', 'N/A')}")
            print(f"   Status: {media.get('status', 'N/A')}")
            print(f"   Episodes: {media.get('episodes', '?')}")
            
            print("\n" + "=" * 80)
            print("\n🎯 NEXT AIRING EPISODE:")
            next_ep = media.get("nextAiringEpisode")
            if next_ep:
                print(f"   Episode: {next_ep.get('episode')}")
                print(f"   Airing At (Unix): {next_ep.get('airingAt')}")
                print(f"   Time Until Airing: {next_ep.get('timeUntilAiring')} seconds")
                
                # Convert to readable date
                from datetime import datetime
                airing_time = datetime.fromtimestamp(next_ep.get('airingAt', 0))
                print(f"   Date: {airing_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("   No upcoming episode")
            
            print("\n" + "=" * 80)
            print("\n📅 AIRING SCHEDULE:")
            airing_schedule = media.get("airingSchedule", {})
            nodes = airing_schedule.get("nodes", [])
            page_info = airing_schedule.get("pageInfo", {})
            
            print(f"   Total Episodes in Schedule: {page_info.get('total', 0)}")
            print(f"   Showing: {len(nodes)} episodes")
            
            if nodes:
                print("\n   Episodes:")
                for ep in nodes[:5]:  # Chỉ hiển thị 5 episode đầu
                    from datetime import datetime
                    airing_time = datetime.fromtimestamp(ep.get('airingAt', 0))
                    print(f"   - Episode {ep.get('episode')}: {airing_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("   No airing schedule available")
            
            print("\n" + "=" * 80)
            print("\n🔍 Full JSON Response:")
            print(json.dumps(media, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"❌ Lỗi khi gọi API: {e}")