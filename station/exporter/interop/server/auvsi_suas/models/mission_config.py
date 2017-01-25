"""Mission configuration model."""

import itertools
import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from auvsi_suas.patches.simplekml_patch import Color
from auvsi_suas.patches.simplekml_patch import AltitudeMode
from auvsi_suas.models import distance
from auvsi_suas.models import units
from fly_zone import FlyZone
from gps_position import GpsPosition
from mission_clock_event import MissionClockEvent
from moving_obstacle import MovingObstacle
from stationary_obstacle import StationaryObstacle
from takeoff_or_landing_event import TakeoffOrLandingEvent
from target import Target
from target import TargetEvaluator
from time_period import TimePeriod
from uas_telemetry import UasTelemetry
from waypoint import Waypoint

# Logging for the module
logger = logging.getLogger(__name__)


class MissionConfig(models.Model):
    """The details for the mission.

    Attributes:
        is_active: Whether the mission is active. Only one mission can be
            active at a time.
        home_pos: The home position for use as a reference point. Should be the
            tents.
        fly_zones: Valid areas for the UAS to fly.
        mission_waypoints: The waypoints that define the mission waypoint path
        search_grid_points: The polygon that defines the search grid.
        targets: The judge created targets.
        emergent_last_known_pos: The last known position of the emergent target.
        off_axis_target_pos: Off-axis target position.
        air_drop_pos: The air drop position.
        stationary_obstacles: The stationary obstacles.
        moving_obstacles: The moving obstacles.
    """
    is_active = models.BooleanField(default=False)
    home_pos = models.ForeignKey(GpsPosition,
                                 related_name="missionconfig_home_pos")
    fly_zones = models.ManyToManyField(FlyZone)
    mission_waypoints = models.ManyToManyField(
        Waypoint,
        related_name='missionconfig_mission_waypoints')
    search_grid_points = models.ManyToManyField(
        Waypoint,
        related_name='missionconfig_search_grid_points')
    targets = models.ManyToManyField(Target,
                                     related_name='missionconfig_targets')
    emergent_last_known_pos = models.ForeignKey(
        GpsPosition,
        related_name='missionconfig_emergent_last_known_pos')
    off_axis_target_pos = models.ForeignKey(
        GpsPosition,
        related_name='missionconfig_off_axis_target_pos')
    air_drop_pos = models.ForeignKey(GpsPosition,
                                     related_name='missionconfig_air_drop_pos')
    stationary_obstacles = models.ManyToManyField(StationaryObstacle)
    moving_obstacles = models.ManyToManyField(MovingObstacle)

    def __unicode__(self):
        """Descriptive text for use in displays."""
        mission_waypoints = ['%s' % wpt.__unicode__()
                             for wpt in self.mission_waypoints.all()]

        search_grid = ['%s' % wpt.__unicode__()
                       for wpt in self.search_grid_points.all()]

        stationary_obstacles = ['%s' % obst.__unicode__()
                                for obst in self.stationary_obstacles.all()]

        moving_obstacles = ['%s' % obst.__unicode__()
                            for obst in self.moving_obstacles.all()]

        return unicode(
            'MissionConfig (pk:%s, is_active: %s, home_pos:%s, '
            'mission_waypoints:%s, search_grid:%s, '
            'emergent_lkp:%s, off_axis:%s, '
            'air_drop_pos:%s, stationary_obstacles:%s, moving_obstacles:%s)' %
            (str(self.pk), str(self.is_active), self.home_pos.__unicode__(),
             mission_waypoints, search_grid,
             self.emergent_last_known_pos.__unicode__(),
             self.off_axis_target_pos.__unicode__(),
             self.air_drop_pos.__unicode__(), stationary_obstacles,
             moving_obstacles))

    def satisfied_waypoints(self, uas_telemetry_logs):
        """Determines whether the UAS satisfied the waypoints.

        Waypoints must be satisfied in order. The entire pattern may be
        restarted at any point. The best (most waypoints satisfied) attempt
        will be returned.

        Assumes that waypoints are at least
        settings.SATISFIED_WAYPOINT_DIST_MAX_FT apart.

        Args:
            uas_telemetry_logs: A list of UAS Telemetry logs.
        Returns:
            best: Dictionary of distance to waypoints of the highest scoring
                attempt.
            scores: Dictionary of individual waypoint scores of the highest
                scoring attempt.
            closest: Dictionary of closest approach distances to
                each waypoint.
        """
        # Use a common projection in distance_to_line based on the home
        # position.
        zone, north = distance.utm_zone(self.home_pos.latitude,
                                        self.home_pos.longitude)
        utm = distance.proj_utm(zone, north)

        waypoints = self.mission_waypoints.order_by('order')

        best = {}
        current = {}
        closest = {}

        def score_waypoint(distance):
            """Scores a single waypoint."""
            return max(
                0, float(settings.SATISFIED_WAYPOINT_DIST_MAX_FT - distance) /
                settings.SATISFIED_WAYPOINT_DIST_MAX_FT)

        def score_waypoint_sequence(sequence):
            """Returns scores given distances to a sequence of waypoints."""
            score = {}
            for i in range(0, len(waypoints)):
                score[i] = \
                    score_waypoint(sequence[i]) if i in sequence else 0.0
            return score

        def best_run(prev_best, current):
            """Returns the best of the current run and the previous best."""
            prev_best_scores = score_waypoint_sequence(prev_best)
            current_scores = score_waypoint_sequence(current)
            if sum(current_scores.values()) > sum(prev_best_scores.values()):
                return current, current_scores
            return prev_best, prev_best_scores

        prev_wpt, curr_wpt = -1, 0

        for uas_log in uas_telemetry_logs:
            # At any point the UAV may restart the waypoint pattern, at which
            # point we reset the counters.
            d0 = uas_log.uas_position.distance_to(waypoints[0].position)
            if d0 < settings.SATISFIED_WAYPOINT_DIST_MAX_FT:
                best = best_run(best, current)[0]

                # Reset current to default values.
                current = {}
                prev_wpt, curr_wpt = -1, 0

            # The UAS may pass closer to the waypoint after achieving the capture
            # threshold. so continue to look for better passes of the previous
            # waypoint until the next is reched.
            if prev_wpt >= 0:
                dp = uas_log.uas_position.distance_to(waypoints[
                    prev_wpt].position)
                if dp < closest[prev_wpt]:
                    closest[prev_wpt] = dp
                    current[prev_wpt] = dp

            # If the UAS has satisfied all of the waypoints, await starting the
            # waypoint pattern again.
            if curr_wpt >= len(waypoints):
                continue

            d = uas_log.uas_position.distance_to(waypoints[curr_wpt].position)
            if curr_wpt not in closest or d < closest[curr_wpt]:
                closest[curr_wpt] = d

            if d < settings.SATISFIED_WAYPOINT_DIST_MAX_FT:
                current[curr_wpt] = d
                curr_wpt += 1
                prev_wpt += 1

        best, scores = best_run(best, current)
        return best, scores, closest

    def evaluate_teams(self, users=None):
        """Evaluates the teams (non admin users) of the competition.

        Args:
            users: Optional list of users to eval. If None will evaluate all.
        Returns:
            A map from user to evaluate data. The evaluation data has the
            following map structure:
            {
                'mission_clock_time': Seconds spent on mission clock,
                'waypoints_satisfied': {
                    id: Boolean,
                }
                'out_of_bounds_time': Seconds spent out of bounds,
                'targets': Data from TargetEvaluation,
                'uas_telem_time': {
                    'max': Value,
                    'avg': Value,
                },
                'stationary_obst_collision': {
                    id: Boolean
                },
                'moving_obst_collision': {
                    id: Boolean
                }
                'warnings': [
                    "String message."
                ],
            }
        """
        # Start a results map from user to evaluation data
        results = {}

        # If not provided, eval all users.
        if users is None:
            users = User.objects.all()

        logger.info('Starting team evaluations.')
        for user in users:
            # Ignore admins.
            if user.is_superuser:
                continue
            logger.info('Evaluation starting for user: %s.' % user.username)

            # Start the evaluation data structure.
            eval_data = results.setdefault(user, {})
            warnings = []
            eval_data['warnings'] = warnings

            # Calculate the total mission clock time.
            mission_clock_time = 0
            missions = MissionClockEvent.missions(user)
            for mission in missions:
                duration = mission.duration()
                if duration is None:
                    warnings.append('Infinite duration mission clock.')
                else:
                    mission_clock_time += duration.total_seconds()
            eval_data['mission_clock_time'] = mission_clock_time

            # Find the user's flights.
            flight_periods = TakeoffOrLandingEvent.flights(user)
            for period in flight_periods:
                if period.duration() is None:
                    warnings.append('Infinite duration flight period.')
            uas_period_logs = [
                UasTelemetry.dedupe(logs)
                for logs in UasTelemetry.by_time_period(user, flight_periods)
            ]
            uas_logs = list(itertools.chain.from_iterable(uas_period_logs))
            if not uas_logs:
                warnings.append('No UAS telemetry logs.')

            # Determine if the uas hit the waypoints.
            waypoint_closest_for_scores, waypoint_scores, closest_approaches = \
                self.satisfied_waypoints(uas_logs)
            eval_data['waypoint_closest_for_scores'] = \
                waypoint_closest_for_scores
            eval_data['waypoint_scores'] = waypoint_scores
            eval_data['waypoint_closest_approaches'] = closest_approaches

            # Determine if the uas went out of bounds. This must be done for
            # each period individually so time between periods isn't counted as
            # out of bounds time. Note that this calculates reported time out
            # of bounds, not actual or possible time spent out of bounds.
            total_out_of_bounds_time = 0
            total_boundary_violations = 0
            for logs in uas_period_logs:
                boundary_violations, out_of_bounds_time = FlyZone.out_of_bounds(
                    self.fly_zones.all(), logs)
                total_out_of_bounds_time += out_of_bounds_time
                total_boundary_violations += boundary_violations
            eval_data['out_of_bounds_time'] = total_out_of_bounds_time
            eval_data['boundary_violations'] = total_boundary_violations

            # Evaluate the targets.
            eval_data['targets'] = {}
            user_targets = Target.objects.filter(user=user).all()
            target_sets = {
                'manual': [t for t in user_targets if not t.autonomous],
                'auto': [t for t in user_targets if t.autonomous],
            }
            for target_set, targets in target_sets.iteritems():
                evaluator = TargetEvaluator(targets, self.targets.all())
                eval_data['targets'][target_set] = evaluator.evaluation_dict()

            # Determine interop telemetry rates.
            uas_telemetry_times = UasTelemetry.rates(
                user,
                flight_periods,
                time_period_logs=uas_period_logs)
            eval_data['uas_telem_times'] = {
                'max': uas_telemetry_times[0],
                'avg': uas_telemetry_times[1]
            }

            # Determine collisions with stationary and moving obstacles.
            stationary_collisions = eval_data.setdefault(
                'stationary_obst_collision', {})
            for obst in self.stationary_obstacles.all():
                collision = obst.evaluate_collision_with_uas(uas_logs)
                stationary_collisions[obst.pk] = collision

            moving_collisions = eval_data.setdefault('moving_obst_collision',
                                                     {})
            for obst in self.moving_obstacles.all():
                collision = obst.evaluate_collision_with_uas(uas_logs)
                moving_collisions[obst.pk] = collision

        return results

    def json(self, is_superuser):
        """Return a dict, for conversion to JSON."""
        ret = {
            'id': self.pk,
            'active': self.is_active,
            'home_pos': {
                'latitude': self.home_pos.latitude,
                'longitude': self.home_pos.longitude,
            },
            "fly_zones": [],  # Filled in below
            "mission_waypoints": [],  # Filled in below
            "search_grid_points": [],  # Filled in below
            'off_axis_target_pos': {
                'latitude': self.off_axis_target_pos.latitude,
                'longitude': self.off_axis_target_pos.longitude,
            },
            "emergent_last_known_pos": {
                "latitude": self.emergent_last_known_pos.latitude,
                "longitude": self.emergent_last_known_pos.longitude,
            },
            'air_drop_pos': {
                'latitude': self.air_drop_pos.latitude,
                'longitude': self.air_drop_pos.longitude,
            },
        }
        for zone in self.fly_zones.all():
            pts = [
                {
                    "latitude": bpt.position.gps_position.latitude,
                    "longitude": bpt.position.gps_position.longitude,
                    "order": bpt.order
                } for bpt in zone.boundary_pts.order_by('order')
            ]
            ret['fly_zones'].append({
                "boundary_pts": pts,
                "altitude_msl_min": zone.altitude_msl_min,
                "altitude_msl_max": zone.altitude_msl_max
            })
        for waypoint in self.mission_waypoints.all():
            ret['mission_waypoints'].append({
                'order': waypoint.order,
                'latitude': waypoint.position.gps_position.latitude,
                'longitude': waypoint.position.gps_position.longitude,
                'altitude_msl': waypoint.position.altitude_msl,
            })
        for point in self.search_grid_points.all():
            ret['search_grid_points'].append({
                'order': point.order,
                'latitude': point.position.gps_position.latitude,
                'longitude': point.position.gps_position.longitude,
                'altitude_msl': point.position.altitude_msl,
            })
        if not is_superuser:
            return ret

        ret.update({
            'stationary_obstacles': [],  # Filled in below
            'moving_obstacles': [],  # Filled in below
        })
        for obst in self.stationary_obstacles.all():
            ret['stationary_obstacles'].append({
                'latitude': obst.gps_position.latitude,
                'longitude': obst.gps_position.longitude,
                'cylinder_radius': obst.cylinder_radius,
                'cylinder_height': obst.cylinder_height,
            })
        for obst in self.moving_obstacles.all():
            ret['moving_obstacles'].append({
                'speed_avg': obst.speed_avg,
                'sphere_radius': obst.sphere_radius,
            })
        return ret

    @classmethod
    def kml_all(cls, kml, missions=None):
        """
        Appends kml nodes describing all mission configurations.

        Args:
            kml: A simpleKML Container to which the mission data will be added
            missions: Optional list of mission for which to generate KML. If
                None, it will use all missions.
        """
        if not missions:
            missions = MissionConfig.objects.all()

        for mission in missions:
            mission.kml(kml)

    def kml(self, kml):
        """
        Appends kml nodes describing this mission configurations.

        Args:
            kml: A simpleKML Container to which the mission data will be added
        """
        mission_name = 'Mission {}'.format(self.pk)
        kml_folder = kml.newfolder(name=mission_name)

        # Static Points
        locations = {
            'Home Position': self.home_pos,
            'Emergent LKP': self.emergent_last_known_pos,
            'Off Axis': self.off_axis_target_pos,
            'Air Drop': self.air_drop_pos,
        }
        for key, point in locations.iteritems():
            gps = (point.longitude, point.latitude)
            wp = kml_folder.newpoint(name=key, coords=[gps])
            wp.description = str(point)

        # Waypoints
        waypoints_folder = kml_folder.newfolder(name='Waypoints')
        linestring = waypoints_folder.newlinestring(name='Waypoints')
        waypoints = []
        waypoint_num = 1
        for waypoint in self.mission_waypoints.all():
            gps = waypoint.position.gps_position
            coord = (gps.longitude, gps.latitude,
                     units.feet_to_meters(waypoint.position.altitude_msl))
            waypoints.append(coord)

            # Add waypoint marker
            wp = waypoints_folder.newpoint(name=str(waypoint_num),
                                           coords=[coord])
            wp.description = str(waypoint)
            wp.altitudemode = AltitudeMode.absolute
            wp.extrude = 1
            wp.visibility = False
            waypoint_num += 1
        linestring.coords = waypoints

        # Waypoints Style
        linestring.altitudemode = AltitudeMode.absolute
        linestring.extrude = 1
        linestring.style.linestyle.color = Color.black
        linestring.style.polystyle.color = Color.changealphaint(100,
                                                                Color.green)

        # Search Area
        search_area_folder = kml_folder.newfolder(name='Search Area')
        search_area = []
        search_area_num = 1
        for point in self.search_grid_points.all():
            gps = point.position.gps_position
            coord = (gps.longitude, gps.latitude,
                     units.feet_to_meters(point.position.altitude_msl))
            search_area.append(coord)

            # Add boundary marker
            wp = search_area_folder.newpoint(name=str(search_area_num),
                                             coords=[coord])
            wp.description = str(point)
            wp.visibility = False
            search_area_num += 1
        if search_area:
            # Create search area polygon.
            pol = search_area_folder.newpolygon(name='Search Area')
            search_area.append(search_area[0])
            pol.outerboundaryis = search_area
            # Search Area Style.
            pol.style.linestyle.color = Color.black
            pol.style.linestyle.width = 2
            pol.style.polystyle.color = Color.changealphaint(50, Color.blue)

        # Stationary Obstacles
        stationary_obstacles_folder = kml_folder.newfolder(
            name='Stationary Obstacles')
