import os
import sqlite3
import csv
import datetime

class InfuseDatabase(object):
    def __init__(self, dbPath):
        self.dbPath = os.path.abspath(dbPath)
        self.cursor = None

        print(f'Opening catalog database at: {self.dbPath}')
        self._open_db()

    def _open_db(self):
        self.connection = sqlite3.connect(self.dbPath)
        self.connection.row_factory = sqlite3.Row
        
        if self.connection:
            self.cursor = self.connection.cursor()

    def get_files(self):
        command = '''SELECT ItemId,
                        Path, 
                        Label, 
                        SeriesTitle
                     FROM FileIndex
                '''
        values = []
        self.cursor.execute(command, values)

        records = self.cursor.fetchall()

        return records

    def get_movies(self):
        command = '''SELECT FileIndex.ItemId,
                        FileIndex.Path, 
                        FileIndex.Label, 
                        meta_movie.Title,
                        meta_movie.ReleaseDate,
                        meta_movie.DurationSec,
                        meta_movie.TmdbID,
                        meta_movie.ImdbID,
                        meta_movie.VideoWidth,
                        meta_movie.VideoHeight,
                        meta_movie.VideoCodec
                     FROM FileIndex
                     JOIN meta_movie on FileIndex.ItemId = meta_movie.ItemId
                     ORDER BY meta_movie.Title
                '''
        values = []
        self.cursor.execute(command, values)

        records = self.cursor.fetchall()

        return records

    def get_tv(self):
        command = '''SELECT FileIndex.ItemId,
                        FileIndex.Path, 
                        FileIndex.Label, 
                        meta_tvshow.SeriesName,
                        meta_tvshow.SeasonName,
                        meta_tvshow.SeasonNumber,
                        meta_tvshow.EpisodeNumber,
                        meta_tvshow.Title,
                        meta_tvshow.AiredDate,
                        meta_tvshow.DurationSec,
                        meta_tvshow.TmdbID,
                        meta_tvshow.ImdbID,
                        meta_tvshow.VideoWidth,
                        meta_tvshow.VideoHeight,
                        meta_tvshow.VideoCodec
                     FROM FileIndex
                     JOIN meta_tvshow on FileIndex.ItemId = meta_tvshow.ItemId
                     ORDER BY meta_tvshow.SeriesName, meta_tvshow.SeasonNumber, meta_tvshow.EpisodeNumber
                '''
        values = []
        self.cursor.execute(command, values)

        records = self.cursor.fetchall()

        return records

def parse_movie_records(movie_records, share_path_prefix=None):
    movies = {}

    for i, record in enumerate(movie_records, 1):
        if i % 100 == 0:
            print(f'Processing record {i}/{len(movie_records)}')

        if not record['Title']:
            continue
        if record['ReleaseDate']:
            release_datetime = datetime.datetime.fromtimestamp(record['ReleaseDate'], datetime.timezone.utc)
            release_year = release_datetime.year 
        else:
            release_year = None

        if share_path_prefix:
            full_path = os.path.join(share_path_prefix, record['path'][1:])
            if os.path.isdir(full_path):
                files = os.listdir(full_path)
            else:
                files = [full_path]
        else:
            files = [record['Path']]

        formats = set()
        for file in files:
            if 'dvd' in file.lower():
                formats.add('dvd')
            elif 'uhd' in file.lower():
                formats.add('uhd')
            elif 'bluray' in file.lower():
                formats.add('bluray')

        if not movies.get(record['TmdbID']):
            movies[record['TmdbID']] = {
                'Title': record['Title'],
                'ReleaseDateTime': release_datetime,
                'TmdbID': record['TmdbID'],
                'ImdbID': record['ImdbID'],
                'DurationSec': record['DurationSec'],
                'VideoWidth': record['VideoWidth'],
                'VideoHeight': record['VideoHeight'],
                'VideoCodec': record['VideoCodec'],
                'Files': set(files),
                'Formats': formats
            }
        else:
            movies[record['TmdbID']]['Files'].add(full_path)
            movies[record['TmdbID']]['Formats'].update(formats)

    sorted_movies = sorted(movies.values(), key=lambda x: (x['Title'], x['ReleaseDateTime']))

    return sorted_movies

def parse_tv_show_records(tv_records):
    tv_shows = {}

    for i, record in enumerate(tv_records, 1):
        if i % 200 == 0:
            print(f'Processing record {i}/{len(tv_records)}')

        if not record['TmdbID']:
            continue

        if record['AiredDate']:
            aired_datetime = datetime.datetime.fromtimestamp(record['AiredDate'], datetime.timezone.utc)
            aired_year = aired_datetime.year 
        else:
            aired_year = None

        full_path = os.path.join('/Volumes', record['path'][1:])
        # if os.path.isdir(full_path):
        #     raise ("TV shows should not be directories, please check your database.")
        
        if 'dvd' in full_path.lower():
            video_format = 'dvd'
        elif 'uhd' in full_path.lower():
            video_format = 'uhd'
        elif 'bluray' in full_path.lower():
            video_format = 'bluray'
        else:
            video_format = 'unknown'

        key = (record['TmdbID'], record['SeasonNumber'], record['EpisodeNumber'])
        if key not in tv_shows:
            tv_shows[key] = {
                'SeriesName': record['SeriesName'],
                'SeasonName': record['SeasonName'],
                'SeasonNumber': record['SeasonNumber'],
                'EpisodeNumber': record['EpisodeNumber'],
                'Title': record['Title'],
                'AiredDateTime': aired_datetime,
                'TmdbID': record['TmdbID'],
                'ImdbID': record['ImdbID'],
                'DurationSec': record['DurationSec'],
                'VideoWidth': record['VideoWidth'],
                'VideoHeight': record['VideoHeight'],
                'VideoCodec': record['VideoCodec'],
                'Files': [full_path],
                'Formats': set([video_format])
            }
        else:
            tv_shows[key]['Files'].append(full_path)
            tv_shows[key]['Formats'].add(video_format)

    sorted_tv_shows = sorted(tv_shows.values(), key=lambda x: (x['SeriesName'], x['SeasonNumber'], x['EpisodeNumber']))

    return sorted_tv_shows

def parse_tv_shows(tv_show_episodes):
    tv_show_seasons = {}

    for episode in tv_show_episodes:
        key = (episode['TmdbID'], episode['SeasonNumber'])
        if int(episode['SeasonNumber']) > 0 and int(episode['EpisodeNumber']) >= 900:
            continue
        if key not in tv_show_seasons:
            tv_show_seasons[key] = {
                'SeriesName': episode['SeriesName'],
                'SeasonName': episode['SeasonName'],
                'SeasonNumber': episode['SeasonNumber'],
                'AiredDateTimes': set([episode['AiredDateTime']]),
                'TmdbID': episode['TmdbID'],
                'ImdbID': episode['ImdbID'],
                'Episodes': set([episode['EpisodeNumber']]),
                'Files': episode['Files'],
                'Formats': episode['Formats'],
            }
        else:
            tv_show_seasons[key]['Episodes'].add(episode['EpisodeNumber'])
            tv_show_seasons[key]['AiredDateTimes'].add(episode['AiredDateTime'])
            tv_show_seasons[key]['Files'].extend(episode['Files'])
            tv_show_seasons[key]['Formats'].update(episode['Formats'])

    sorted_tv_show_seasons = sorted(tv_show_seasons.values(), key=lambda x: (x['SeriesName'], x['SeasonNumber']))
        
    return sorted_tv_show_seasons

def write_movies_to_csv(sorted_movies):
    with open('infuse_movies.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'ReleaseDate', 'TmdbID', 'ImdbID', 'Formats', 'DurationSec', 'VideoWidth', 'VideoHeight', 'VideoCodec', 'Files']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for movie in sorted_movies:
            sorted_formats = []
            if 'uhd' in movie['Formats']:
                sorted_formats.append('uhd')
            if 'bluray' in movie['Formats']:
                sorted_formats.append('bluray')
            if 'dvd' in movie['Formats']:
                sorted_formats.append('dvd')

            writer.writerow({
                'Title': movie['Title'],
                'ReleaseDate': movie['ReleaseDateTime'].date().isoformat() if movie['ReleaseDateTime'] else None,
                'TmdbID': movie['TmdbID'],
                'ImdbID': movie['ImdbID'],
                'Formats': ', '.join(sorted_formats),
                'DurationSec': movie['DurationSec'],
                'VideoWidth': movie['VideoWidth'],
                'VideoHeight': movie['VideoHeight'],
                'VideoCodec': movie['VideoCodec'],
                'Files': ', '.join(movie['Files']),
            })

def write_tv_show_episodes_to_csv(sorted_tv_shows):
    with open('infuse_tv_shows.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['SeriesName', 'SeasonName', 'SeasonNumber', 'EpisodeNumber', 'Title', 'AiredDate', 'TmdbID', 'ImdbID', 'Formats', 'DurationSec', 'VideoWidth', 'VideoHeight', 'VideoCodec', 'Files']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for show in sorted_tv_shows:
            sorted_formats = []
            if 'uhd' in show['Formats']:
                sorted_formats.append('uhd')
            if 'bluray' in show['Formats']:
                sorted_formats.append('bluray')
            if 'dvd' in show['Formats']:
                sorted_formats.append('dvd')
            if 'unknown' in show['Formats']:
                sorted_formats.append('unknown')

            writer.writerow({
                'SeriesName': show['SeriesName'],
                'SeasonName': show['SeasonName'],
                'SeasonNumber': show['SeasonNumber'],
                'EpisodeNumber': show['EpisodeNumber'],
                'Title': show['Title'],
                'AiredDate': show['AiredDateTime'].date().isoformat() if show['AiredDateTime'] else None,
                'TmdbID': show['TmdbID'],
                'ImdbID': show['ImdbID'],
                'Formats': ', '.join(sorted_formats),
                'DurationSec': show['DurationSec'],
                'VideoWidth': show['VideoWidth'],
                'VideoHeight': show['VideoHeight'],
                'VideoCodec': show['VideoCodec'],
                'Files': ', '.join(show['Files']),
            })

def write_tv_show_seasons_to_csv(sorted_tv_show_seasons):
    with open('infuse_tv_show_seasons.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['SeriesName', 'SeasonName', 'SeasonNumber', 'Num Episodes', 'Episodes', 'FirstAirDate', 'LastAirDate', 'Formats', 'TmdbID', 'ImdbID', 'Files']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for season in sorted_tv_show_seasons:
            first_air_date = min(season['AiredDateTimes']).date().isoformat() if season['AiredDateTimes'] else None
            last_air_date = max(season['AiredDateTimes']).date().isoformat() if season['AiredDateTimes'] else None
            writer.writerow({
                'SeriesName': season['SeriesName'],
                'SeasonName': season['SeasonName'],
                'SeasonNumber': season['SeasonNumber'],
                'FirstAirDate': first_air_date,
                'LastAirDate': last_air_date,
                'TmdbID': season['TmdbID'],
                'ImdbID': season['ImdbID'],
                'Num Episodes': len(season['Episodes']),
                'Episodes': ', '.join(map(str, sorted(season['Episodes']))),
                'Files': ', '.join(season['Files']),
                'Formats': ', '.join(sorted(season['Formats'])),
            })

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--db_path', help='Path to the Infuse database file')
    parser.add_argument('--share_path_prefix', help='Path prefix to the NAS share')
    args = parser.parse_args()

    if not args.db_path:
        args.db_path = os.path.expanduser('~/Library/Containers/com.firecore.infuse/Data/Library/Preferences/InternalPrefs/com.firecore.media.meta.db')
        print('\nNo database path provided, using default path.')
        
    database = InfuseDatabase(args.db_path)

    movie_records = database.get_movies()
    print(f'\n*** Movie records in database: {len(movie_records)}')

    sorted_movies = parse_movie_records(movie_records, args.share_path_prefix)
    print(f'Total unique movies found: {len(sorted_movies)}')

    print(f'Saving to infuse_movies.csv...')
    write_movies_to_csv(sorted_movies)

    tv_records = database.get_tv()
    print(f'\n*** TV show records in database: {len(tv_records)}')

    sorted_tv_show_episodes = parse_tv_show_records(tv_records)
    print(f'Total unique TV show episodes found: {len(sorted_tv_show_episodes)}')
    
    print(f'Saving to infuse_tv_show_episodes.csv...')
    write_tv_show_episodes_to_csv(sorted_tv_show_episodes)

    sorted_tv_show_seasons = parse_tv_shows(sorted_tv_show_episodes)
    print(f'Total unique TV show seasons found: {len(sorted_tv_show_seasons)}')

    print(f'Saving to infuse_tv_show_seasons.csv...')
    write_tv_show_seasons_to_csv(sorted_tv_show_seasons)
