#!/usr/bin/env python2.7
# coding: utf-8
import logging
import os
import sys
from logging.config import dictConfig
from multiprocessing import active_children
from time import sleep

from lib.worker import worker
from source.lib import utils

logger = logging.getLogger('redirect_checker')


def main_loop_iteration(config, parent_pid):
    if utils.check_network_status(config.CHECK_URL, config.HTTP_TIMEOUT):
        required_workers_count = config.WORKER_POOL_SIZE - len(
            active_children())
        if required_workers_count > 0:
            logger.info(
                'Spawning {} workers'.format(required_workers_count))
            utils.spawn_workers(
                num=required_workers_count,
                target=worker,
                args=(config,),
                parent_pid=parent_pid
            )
    else:
        logger.critical('Network is down. stopping workers')
        for c in active_children():
            c.terminate()


def main_loop(config):
    logger.info(
        u'Run main loop. Worker pool size={}. Sleep time is {}.'.format(
            config.WORKER_POOL_SIZE, config.SLEEP
        ))
    parent_pid = os.getpid()
    while True:
        main_loop_iteration(config, parent_pid)

        sleep(config.SLEEP)


def prepare(args):
    if args.daemon:
        utils.daemonize()
    if args.pidfile:
        utils.create_pidfile(args.pidfile)
    config = utils.load_config_from_pyfile(
        os.path.realpath(os.path.expanduser(args.config))
    )
    dictConfig(config.LOGGING)
    return config


def main(argv):
    args = utils.parse_cmd_args(argv[1:])
    config = prepare(args)

    main_loop(config)

    return config.EXIT_CODE


if __name__ == '__main__':
    sys.exit(main(sys.argv))
