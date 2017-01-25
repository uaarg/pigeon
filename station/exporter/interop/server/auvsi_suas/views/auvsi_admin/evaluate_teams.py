"""Admin automatic evaluation of teams view."""

import copy
import cStringIO
import csv
from auvsi_suas.models.mission_config import MissionConfig
from auvsi_suas.views import logger
from auvsi_suas.views.decorators import require_superuser
from auvsi_suas.views.missions import mission_for_request
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import HttpResponseServerError
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View


class EvaluateTeamsBase(View):
    """Evaluates the teams and delegates to subclasses for format."""

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(EvaluateTeamsBase, self).dispatch(*args, **kwargs)

    def format_response(self, user_eval_data):
        """Format and return the response for given evaluation dat.a"""
        logging.fatal('Not implemented.')

    def get(self, request):
        logger.info('Admin downloading team evaluation.')

        # Get the mission to evaluate a team for.
        mission, error = mission_for_request(request.GET)
        if error:
            logger.warning('Could not get mission to evaluate teams.')
            return error

        # Get the optional team to eval.
        users = None
        if 'team' in request.GET:
            try:
                team = int(request.GET['team'])
                users = [User.objects.get(pk=team)]
            except TypeError:
                return HttpResponseBadRequest('Team not an ID.')
            except User.DoesNotExist:
                return HttpResponseNotFound('Team not found.')

        # Get the eval data for the teams
        user_eval_data = mission.evaluate_teams(users)
        if not user_eval_data:
            logger.warning('No data for team evaluation.')
            return HttpResponseServerError(
                'Could not get user evaluation data.')
        # Convert to username key-d map.
        user_eval_data = {u.username: d for u, d in user_eval_data.iteritems()}
        return self.format_response(user_eval_data)


class EvaluateTeamsJson(EvaluateTeamsBase):
    """Evaluates the teams and returns JSON."""

    def format_response(self, user_eval_data):
        return JsonResponse(user_eval_data)


class EvaluateTeamsCsv(EvaluateTeamsBase):
    """Evaluates the teams and returns CSV."""

    def format_response(self, user_eval_data):
        # Reformat to column oriented
        user_col_data = {}
        for (username, eval_data) in user_eval_data.iteritems():
            col_data = user_col_data.setdefault(username, {})
            col_data['username'] = username
            work_queue = [([], eval_data)]
            while len(work_queue) > 0:
                (cur_prefixes, cur_map) = work_queue.pop()
                for (key, val) in cur_map.iteritems():
                    new_prefixes = copy.copy(cur_prefixes)
                    new_prefixes.append(str(key))
                    if isinstance(val, dict):
                        work_queue.append((new_prefixes, val))
                    else:
                        column_key = '.'.join(new_prefixes)
                        if isinstance(val, list):
                            col_data[column_key] = ','.join(val)
                        else:
                            col_data[column_key] = val
        # Get column headers
        col_headers = set()
        for col_data in user_col_data.values():
            for header in col_data.keys():
                col_headers.add(header)
        col_headers = sorted(col_headers)

        # Write output
        csv_output = cStringIO.StringIO()
        writer = csv.DictWriter(csv_output, fieldnames=col_headers)
        writer.writeheader()
        for col_data in user_col_data.values():
            writer.writerow(col_data)
        output = csv_output.getvalue()
        csv_output.close()
        return HttpResponse(output, content_type='text/csv')
