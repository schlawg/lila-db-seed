import pymongo
import random
import argparse
from modules.event import events
from modules.env import env
import modules.forum as forum
import modules.util as util


def update_team_colls() -> None:
    args = env.args
    db = env.db
    do_drop = args.drop == "team" or args.drop == "all"

    if do_drop:
        db.team.drop()
        db.team_member.drop()

    categs: list[forum.Categ] = []
    topics: list[forum.Topic] = []
    posts: list[forum.Post] = []
    teams: list[Team] = []
    all_members: list[TeamMember] = []

    for (team_name, num_team_posts) in zip(
        env.teams, util.random_partition(args.posts, len(env.teams))
    ):
        t = Team(team_name)
        teams.append(t)
        events.add_team(t.createdBy, t.createdAt, t._id, t.name)
        categs.append(forum.Categ(team_name, True))

        team_members = t.create_members()
        for m in team_members:
            if m.user != t.createdBy:
                events.join_team(
                    m.user, util.time_since(t.createdAt), t._id, t.name
                )
        all_members.extend(team_members)
        remaining_topics = env.topics.copy()
        random.shuffle(remaining_topics)
        for num_posts in util.random_partition(
            num_team_posts,
            min(int(num_team_posts / 10) + 1, len(remaining_topics)),
        ):
            if num_posts == 0:
                continue
            t = forum.Topic(remaining_topics.pop(), categs[-1]._id)
            topics.append(t)
            for _ in range(num_posts):
                p = forum.Post(random.choice(team_members).user)
                posts.append(p)
                t.correlate_post(p)
                events.add_post(
                    p.userId,
                    p.createdAt,
                    p._id,
                    t._id,
                    t.name,
                    [u.user for u in team_members],
                )
            categs[-1].add_topic(t)

    if args.no_create:
        return

    util.bulk_write(db.f_categ, categs, do_drop, True)
    util.bulk_write(db.f_topic, topics, do_drop, True)
    util.bulk_write(db.f_post, posts, do_drop, True)
    util.bulk_write(db.team, teams, do_drop)
    util.bulk_write(db.team_member, all_members, do_drop)


class TeamMember:
    def __init__(self, uid: str, teamId: str):
        self._id = uid + "@" + teamId
        self.team = teamId
        self.user = uid
        self.date = util.time_since_days_ago(720)


class Team:
    def __init__(self, name: str):
        self._id = util.normalize_id(name)
        self.name = name
        self.description = env.random_topic()
        self.descPrivate = "All of our dads could beat up YOUR dad."
        self.nbMembers = 1
        self.enabled = True
        self.open = util.chance(0.5)
        self.createdAt = util.time_since_days_ago(1440)
        self.leaders = random.sample(
            env.uids, util.rrange(1, min(len(env.uids), 4))
        )
        self.createdBy = self.leaders[0]
        self.chat = 20  # of course chat and forum are equal to 20.
        self.forum = 20  # wtf else would they possibly be??

    def create_members(self) -> list[TeamMember]:
        users: set[str] = set(self.leaders).union(
            random.sample(env.uids, util.rrange(2, int(len(env.uids) / 4)))
        )
        self.nbMembers = len(users)
        return [TeamMember(user, self._id) for user in users]
