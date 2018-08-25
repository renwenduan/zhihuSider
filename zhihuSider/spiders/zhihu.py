# -*- coding: utf-8 -*-
import scrapy
import json
from scrapy import Spider,Request
from zhihuSider.items import UserItem

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']  # 定义爬虫能爬取的范围
    start_urls = ['http://www.zhihu.com/']  # 开始的url
    start_user = 'hypnova'  # 这是我们传进去的第一个人,我们将从他开始获取他的粉丝,然后获取他粉丝的粉丝,然后获取他粉丝的粉丝的粉丝,然后.....

    # 个人信息接口
    user_info_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'  # 使用.format方法来动态获取每个用户的信息
    # include 内容单独取出来
    user_query = 'locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,avatar_hue,answer_count,articles_count,pins_count,question_count,columns_count,commercial_question_count,favorite_count,favorited_count,logs_count,marked_answers_count,marked_answers_text,message_thread_token,account_status,is_active,is_bind_phone,is_force_renamed,is_bind_sina,is_privacy_protected,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics'

    # 用户关注信息接口
    follower_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    # include 内容单独取出来
    follower_query = 'data[*].is_normal,admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,collapsed_by,suggest_edit,comment_count,can_comment,content,voteup_count,reshipment_settings,comment_permission,mark_infos,created_time,updated_time,review_info,relationship.is_authorized,voting,is_author,is_thanked,is_nothelp,upvoted_followees;data[*].author.badge[?(type=best_answerer)].topics'

    # 关注用户的人接口
    followee_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    # include 内容单独取出来
    followee_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        '''这个方法用来获取启动各个方法'''
        yield Request(self.user_info_url.format(user=self.start_user, include=self.user_query),
                      callback=self.user_info_parse)

        yield Request(self.follower_url.format(user=self.start_user, include=self.follower_query, offset=0, limit=20),
                      callback=self.follower_info_parse)

        yield Request(self.followee_url.format(user=self.start_user, include=self.followee_query, offset=0, limit=20),
                      callback=self.followee_info_parse)

    def user_info_parse(self, response):
        '''用来获取用户个人信息的方法,并将这个人的url_token传递给获取用户粉丝和关注列表的函数以获得这个人的粉丝和关注列表'''

        # 将获取到的Python对象转换为json对象
        result = json.loads(response.text)

        # 实例化一个item用来传递信息
        item = UserItem()

        # 这个方法很有用可以快速取得自己要的内容(json返回),然后在使用判断进行快速赋值
        for field in item.fields:

            # 保证取到了我们定义好的数据而没有定义的数据不会出现
            if field in result.keys():
                # 依次给item赋值
                item[field] = result.get(field)

        # 返回给item
        yield item

        # 将url_token传递给获取用户粉丝列表的函数
        yield Request(
            self.follower_url.format(user=result['url_token'], include=self.follower_query, offset=0, limit=20),
            callback=self.follower_info_parse)

        # 将url_token传递给获取用户关注列表的函数
        yield Request(
            self.followee_url.format(user=result['url_token'], include=self.followee_query, offset=0, limit=20),
            callback=self.followee_info_parse)

    def follower_info_parse(self, response):
        '''当我们得到了用户的关注者后,将这些关注者再次调用这个方法,继续得到关注者, 这里采用了递归的思想'''

        # 将Python对象转换为json对象
        result = json.loads(response.text)

        # 判断返回的数据中是否有data如果有就获取这个人的url,如果没有就去判断是否有下一页
        if 'data' in result.keys():

            # 循环遍历data中的每个人,然后获取他的url_token传给user_info_parse函数处理
            for user in result.get('data'):
                # 传递url_token给个人信息处理函数进行处理
                yield Request(self.user_info_url.format(user=user.get('url_token'), include=self.user_query),
                              callback=self.user_info_parse)

        # 判断是否有下一页
        if 'paging' in result.keys() and result.get('paging').get('is_end') == False:
            '''这里判断用户的列表有么有下一页,这个功能在每次取完本页后调用,没有就结束,有就将下一页的网址传给自己继续获得永不'''
            next_url = result.get('paging').get('next')

            # 有下一页就调用自己将下一页的信息继续获取
            yield Request(next_url, callback=self.follower_info_parse)

    def followee_info_parse(self, response):
        '''这里同上面的分析'''
        result = json.loads(response.text)
        if 'data' in result.keys():
            for user in result.get('data'):
                yield Request(self.user_info_url.format(user=user.get('url_token'), include=self.followee_query),
                              callback=self.user_info_parse)
        if 'paging' in result.keys() and result.get('paging').get('is_end') == False:
            next_url = result.get('paging').get('next')
            yield Request(next_url, callback=self.followee_info_parse)