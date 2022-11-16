#!/usr/bin/env python3
import pymongo
import argparse
import modules.forum as forum
import modules.event as event
import modules.user as user
import modules.blog as blog
import modules.game as game
import modules.team as team
import modules.tour as tour
import modules.insight as insight

from modules.env import env


def main():
    env.set_args(_get_args())

    with _MongoContextMgr(env.args.uri) as db:
        env.db = db
        user.update_user_colls()
        game.update_game_colls()
        tour.update_tour_colls()
        forum.update_forum_colls()
        team.update_team_colls()
        blog.update_blog_colls()
        event.update_event_colls()
        insight.update_insight_coll()


class _MongoContextMgr:
    def __init__(self, uri):
        self.client = pymongo.MongoClient(uri)
        self.client.admin.command(
            "ping"
        )  # should raise an exception if we cant connect
        self.db = self.client.get_default_database()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.client.close()


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="""
            seed lila database with all kinds of spam. using the --drop all
            argument will speed up database creation.  it is highly recommended
            to at least use --drop event on modify runs as event collections
            don't match on upserts, causing them to accumulate. this would be
            default behavior if I was the sort to drop your database collections
            without asking in a script
        """
    )
    parser.add_argument(
        "--uri",
        "-u",
        help="""
            form: --uri="mongodb://user:password@host:port/database?
            authSource=default_db&authMechanism=SCRAM-SHA-256"  (default:
            mongodb://127.0.0.1/lichess)
        """,
        default="mongodb://127.0.0.1/lichess",
    )
    parser.add_argument(
        "--password",
        "-p",
        type=str,
        help="""
            supply your own default password. this is highly recommended for
            exposed dev instances. note: different values may be assigned to
            specific users in data/uids.txt. uids.txt passwords will override this
            argument for the specified user only. (default: password)
        """,
        default="password",
    )
    parser.add_argument(
        "--user-bg",
        "-b",
        type=int,
        help="""
            generated users will have this background set in their associated
            Pref object, 100 = light mode, 200 = dark mode, 400 = transparent
            with random image from data/image_links.txt. (default: 200)
        """,
        default=200,
        choices=[100, 200, 400],
    )
    parser.add_argument(
        "--users",
        type=int,
        help="""
            how many normal users to generate. for large values, spamdb will
            postfix increasing numbers to the uids listed in data/uids.txt.
            special users are always generated and are not affected by this flag.
            users with postfixed numbers get the default password. (default:
            # of users in uids.txt)
        """,
    )
    parser.add_argument(
        "--posts",
        type=int,
        help="""
            approximate number of POSTS generated for both teams and regular
            forums (default: 4000)
        """,
        default=4000,
    )
    parser.add_argument(
        "--blogs",
        type=int,
        help="(default: 20)",
        default=20,
    )
    parser.add_argument(
        "--teams",
        type=int,
        help="(default: # of items in teams.txt)",
    )
    parser.add_argument(
        "--tours",
        type=int,
        default=80,
        help="(default: 80)",
    )
    parser.add_argument(
        "--games",
        type=int,
        help="(default/max = # of objects in game5.bson (around 3000))",
    )
    parser.add_argument(
        "--follow",
        type=float,
        default=0.16,
        help="""
            follow factor is the fraction of all users that each user
            follows. for work on timelines, notifications, friend features,
            you can set this to 1 for a fully connected graph of normal users.
            (default: .16)
        """,
    )
    parser.add_argument(
        "--insights",
        action="store_true",
        help="""
            use this flag to add insights data.  note that you must override
            insight.mongodb.uri=${mongodb.uri} in your application.conf to see
            the insights. (base.conf defaults to a different database).
            """
    )
    parser.add_argument(
        "--no-timeline",
        "-n",
        action="store_true",
        help="""
            timeline entries are constructed with unique object ids from the
            bson module. their ids will not match on subsequent spamdb upserts
            and therefore they keep accumulating until you --drop event or
            --drop all. if you do not wish to drop, you may also prevent entries
            from accumulating by including the --no-timeline argument. this will
            suppress their generation for this run.
        """,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dump-bson",
        type=str,
        help="leave db alone. generate and dump BSONs to provided directory",
    )
    group.add_argument(
        "--dump-json",
        type=str,
        help="leave db alone. generate and dump JSONs to provided directory",
    )
    group.add_argument(
        "--no-create",
        action="store_true",
        help="""
            skip database in/upserts. useful for testing the object generation
            code or just erasing spamdb stuff in conjunction with --drop
        """,
    )
    parser.add_argument(
        "--drop",
        help="""
            drop pre-existing collections prior to any object creation. see module
            code for specific collections dropped by each choice. specify "all" to
            drop ALL collections managed by spamdb (others will be left alone).
        """,
        choices=[
            "all",
            "game",
            "event",
            "forum",
            "team",
            "user",
            "blog",
            "tour",
            "insight",
        ],
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
