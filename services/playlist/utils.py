from sqlalchemy import select, update
from models import User, Group, Tracks, UserTracks, Playlist, Member
from sqlalchemy.orm import sessionmaker
from session import session

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
scope = os.getenv('SPOTIFY_SCOPE')

# Create a Spotipy instance with a new cache path for each user
def create_spotify_instance(cache_path):
    return spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                      client_secret=client_secret,
                                                      redirect_uri=redirect_uri,
                                                      scope=scope,
                                                      cache_path=cache_path))

def get_group_by_id(group_id):
    group = session.query(Group).filter_by(id = group_id).first()

    if group is not None:
        # for member in group.members:
        #     print(member.name)
        print("group found", group)
        return group
    else:
        return None

def get_group_members(group):
    members = session.query(Member).join(User, onclause=Member.user_id==User.id).filter(Member.group_id == group.id).all()

    return members


def get_all_tracks(members):
    # Get list of user_ids of all group members
    if members:
        member_ids = [member.user_id for member in members]
    
    # Get all distinct tracks for all member ids
        all_tracks = session.query(UserTracks) \
                        .join(Tracks, UserTracks.track_id == Tracks.track_id) \
                        .filter(UserTracks.user_id.in_(member_ids)) \
                        .group_by(Tracks.track_id).all()
        
        # Create dict of user to list of tracks
        # user_tracks = {}

        return all_tracks
    else:
        print("No group found")



def create_spotify_playlist(user_id, playlist_id, name, description):
    user = session.query(User).filter_by(id=user_id).first()
    cache_path = f"cache_{user.id}"
    f = open(cache_path, "w")
    os.write(user.cache)
    f.close()

    sp = create_spotify_instance(cache_path)
    spotify_user_id = sp.current_user()['id']
    new_playlist = sp.user_playlist_create(user=spotify_user_id, name=name, public=True, collaborative=False, description=description)

    playlist_url = new_playlist['external_urls']['spotify']

    # playlist = Playlist(id=playlist_id, link=playlist_url)

    session.execute(update(Playlist).where(id=playlist_id), {"link": playlist_url})



def create_playlist(playlist_data):
    # 1. Get group members from playlist_data.group_id
    group = get_group_by_id(playlist_data.id)

    members = get_group_members(group)
    # 2. Get tracks of each member of group
    all_tracks = get_all_tracks(members)

    # 3. Create a list of tracks of length playlist_data.num_tracks from all the tracks for each member
    # playlist_tracks = get_playlist_tracks(all_tracks)

    # 4. Create playlist (empty initially)
    #   a. ENDPOINT:  https://api.spotify.com/v1/users/{user_id}/playlists
    #   b. Req body: name, description, public
    #   c. Response will contain {
    #     "external_urls": {
    #         "spotify": "string"
    #     },
    #     "href": "string",
    #     "id": "string",
    #     "name": "string",
    #     "type": "string",
    #     "uri": "string"
    #     }
    create_resp = create_spotify_playlist(group.owner_id, playlist_data.name.id, playlist_data.name, playlist_data.description)
    
    # 5. Add 3. to 4.
    #   a. ENDPOINT:  https://api.spotify.com/v1/playlists/{playlist_id}/tracks
    #   b. Req body: {"uris": ["string"],"position": 0}
    #   c. Response: {"snapshot_id": "abc"}
    
    
    # 6. Update playlist_data.link with the playlist.external_urls.spotify url string.
    
    
    # 7. return success