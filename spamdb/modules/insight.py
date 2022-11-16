import random
import bson
import base64
import pymongo
import argparse
from modules.event import events
from modules.env import env
import modules.util as util
from datetime import timedelta


def update_insight_coll() -> None:
    args = env.args
    db = env.db
    do_drop = args.drop == "insight" or args.drop == "all"

    if do_drop:
        db.insight.drop()

    insights: list[insight.Insight] = []

    for bson_insight in env.insights:
        bson_insight["u"] = random.choice(env.uids)

    if args.no_create:
        return

    util.bulk_write(db.insight, env.insights, do_drop)
