import HTMLParser
from datetime import datetime, timedelta
import pytz
import random
import re

from database import db
from models import Account, Settings, TopTodayAccount


class Simulator(object):
    def __init__(self):
        self.accounts = {account.subreddit: account
            for account in db.query(Account)}
        self.subreddit = Settings["subreddit"]
        self.mod_account = self.accounts["all"]

    def pick_account_to_comment(self):
        accounts = [a for a in self.accounts.values() if a.can_comment]

        # if any account hasn't commented yet, pick that one
        try:
            return next(a for a in accounts if not a.last_commented)
        except StopIteration:
            pass

        # pick an account from the 25% that commented longest ago
        accounts = sorted(accounts, key=lambda a: a.last_commented)
        num_to_keep = int(len(accounts) * 0.25)
        return random.choice(accounts[:num_to_keep])

    def pick_account_to_submit(self):
        # make a submission based on today's /r/all every 6 hours
        try:
            top_today_account = next(a for a in self.accounts.values()
                if isinstance(a, TopTodayAccount))
        except StopIteration:
            pass
        else:
            now = datetime.now(pytz.utc)
            if now - top_today_account.last_submitted > timedelta(hours=5.5):
                return top_today_account

        accounts = [a for a in self.accounts.values() if a.is_able_to_submit]

        # if any account hasn't submitted yet, pick that one
        try:
            return next(a for a in accounts if not a.last_submitted)
        except StopIteration:
            pass

        # pick an account from the 25% that submitted longest ago
        accounts = sorted(accounts, key=lambda a: a.last_submitted)
        num_to_keep = int(len(accounts) * 0.25)
        return random.choice(accounts[:num_to_keep])

    def make_comment(self):
        account = self.pick_account_to_comment()
        account.train_from_comments()

        # get the newest submission in the subreddit
        subreddit = account.session.get_subreddit(self.subreddit)
        for submission in subreddit.get_new(limit=5):
            if submission.author.name != Settings["owner"]:
                break
        account.post_comment_on(submission)

    def make_submission(self):
        account = self.pick_account_to_submit()
        account.train_from_submissions()
        account.post_submission(self.subreddit)

    def update_leaderboard(self, limit=100):
        session = self.mod_account.session
        subreddit = session.get_subreddit(self.subreddit)

        accounts = sorted(
            [a for a in self.accounts.values() if a.can_comment],
            key=lambda a: a.mean_comment_karma,
            reverse=True,
        )

        leaderboard_md = "\\#|Account|Avg Karma\n--:|:--|--:"
        for rank, account in enumerate(accounts, start=1):
            leaderboard_md += "\n{}|/u/{}|{:.2f}".format(
                rank,
                account.name,
                account.mean_comment_karma,
            )
            if rank >= limit:
                break

        start_delim = "[](/leaderboard-start)"
        end_delim = "[](/leaderboard-end)"
        current_sidebar = subreddit.get_settings()["description"]
        current_sidebar = HTMLParser.HTMLParser().unescape(current_sidebar)
        replace_pattern = re.compile(
            "{}.*?{}".format(re.escape(start_delim), re.escape(end_delim)),
            re.IGNORECASE|re.DOTALL|re.UNICODE,
        )
        new_sidebar = re.sub(
            replace_pattern,
            "{}\n\n{}\n\n{}".format(start_delim, leaderboard_md, end_delim),
            current_sidebar,
        )
        subreddit.update_settings(description=new_sidebar)

        flair_map = [{
            "user": account.name,
            "flair_text": "#{} / {} ({:.2f})".format(
                rank, len(accounts), account.mean_comment_karma),
            } for rank, account in enumerate(accounts, start=1)]
            
        subreddit.set_flair_csv(flair_map)

    def print_accounts_table(self):
        accounts = sorted(self.accounts.values(), key=lambda a: a.added)
        accounts = [a for a in accounts if not isinstance(a, TopTodayAccount)]
        
        print "Subreddit|Added|Posts Comments?|Posts Submissions?"
        print ":--|--:|:--|:--"

        checkmark = "&#10003;"
        for account in accounts:
            print "[{}]({})|{}|{}|{}".format(
                account.subreddit,
                "/u/" + account.name,
                account.added.strftime("%Y-%m-%d"),
                checkmark if account.can_comment else "",
                checkmark if account.can_submit else "",
            )
