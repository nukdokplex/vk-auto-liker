import argparse
import time

import progressbar
import vk_api


def two_factor_handler():
    key = input("Enter authentication code: ")
    remember_device = True

    return key, remember_device


def captcha_handler(captcha):
    key = input(f"Enter captcha code {captcha.get_url()}: ").strip()

    return captcha.try_again(key)


def main(a):
    vk_session = vk_api.VkApi(
        login=a.login,
        password=a.password,
        auth_handler=two_factor_handler,
        captcha_handler=captcha_handler
    )

    try:
        vk_session.auth(reauth=a.reauth, token_only=True)
    except vk_api.AuthError as e:
        print(e)
        return

    vk = vk_session.get_api()
    posts = []
    print("Getting posts to like... ", end="")
    if 100 >= a.count >= 1:
        posts = vk.wall.get(count=a.count, offset=a.offset, owner_id=a.wall_id)['items']
    else:
        tools = vk_api.VkTools(vk_session)
        posts = tools.get_all('wall.get', 100, {'owner_id': a.wall_id})['items']
    print("OK!")

    print(f'Liking {len(posts)} posts... Timeout is {a.timeout} seconds.')
    skip_count = 0
    with progressbar.ProgressBar(max_value=len(posts)) as pb:
        for i, post in enumerate(posts):
            if a.start <= post['date'] <= a.end:
                if post['likes']['user_likes'] != 1:
                    time.sleep(a.timeout)
                    vk.likes.add(type='post', owner_id=post['owner_id'], item_id=post['id'])
                else:
                    skip_count += 1
            else:
                skip_count += 1
            pb.update(i + 1)
    print(f'Successfully liked {len(posts) - skip_count} post(s). Skipped {skip_count} post(s).', end='\n\n')

    print('Have a nice day!')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Likes VKontakte posts on specified wall")
    parser.add_argument("login", type=str, help="Vkontakte login")
    parser.add_argument("password", type=str, help="Vkontakte password")
    parser.add_argument("wall_id", type=int, help="Vkontakte wall id")
    parser.add_argument("-s", "--start", type=int, help="posts from this time will be processed (in unix time format) "
                                                        "(defaults to start of era)", default=0)
    parser.add_argument("-e", "--end", type=int, help="posts before this time will be processed (in unix time format) "
                                                      "(defaults to now)", default=int(time.time()))
    parser.add_argument("-r", "--reauth", help="Forces re-authentication", action="store_true")
    parser.add_argument("--token-only", help="Enables the optimal authentication strategy is only access_token is "
                                             "needed (enabled default)", action="store_true", default=True)
    parser.add_argument("-c", "--count", type=int, help="Max count of latest posts that will be processed "
                                                        "(defaults to all posts, may be dangerous)", default=-1)
    parser.add_argument("-o", "--offset", type=int, help="Offset of posts that will be processed (defaults to 0)",
                        default=0)
    parser.add_argument("-t", "--timeout", type=int, help="Timeout of post liking in seconds (defaults to 20)",
                        default=20)
    args = parser.parse_args()
    if 1 > args.count > 100 and args.count != -1:
        raise ValueError("Count must be greater than or equal to 1 and must not exceed 100")
    if args.offset < 0:
        raise ValueError("Offset must be zero or positive integer")
    if args.start < 0 or args.end < 0:
        raise ValueError("Start and end must be zero or positive integer")
    if args.start > args.end:
        raise ValueError("Start must not be greater than end")

    main(args)
