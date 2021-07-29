# coding: utf-8
import json
import logging
from collections import defaultdict

from django import forms
from django.utils.translation import ugettext_lazy as _

from sentry.plugins.bases import notify
from sentry.http import safe_urlopen
from sentry.utils.safe import safe_execute

from . import __version__, __doc__ as package_doc


class LarkNotificationsOptionsForm(notify.NotificationConfigurationForm):
    webhook = forms.CharField(
        label=_('Webhook'),
        widget=forms.TextInput(attrs={'placeholder': 'https://open.feishu.cn/open-apis/bot/hook/xxx'}),
        help_text=_('Read more: https://getfeishu.cn/hc/en-us/articles/360024984973-Use-Bots-in-group-chat'),
    )
    message_template = forms.CharField(
        label=_('Message template'),
        widget=forms.Textarea(attrs={'class': 'span4'}),
        help_text=_('Set in standard python\'s {}-format convention, available names are: '
                    '{project_name}, {url}, {title}, {message}, {tag[%your_tag%]}'),
        initial="{header} 【项目】{project_name} 【用户】{user} 【环境】{tag['environment']} 【版本】{tag['sentry:release']}"
                " 【内容】{message} <btn:点击查看详情>{url}"
    )


class LarkNotificationsPlugin(notify.NotificationPlugin):
    title = 'Lark Sentry Notifications'
    slug = 'lark_sentry'
    description = package_doc
    version = __version__
    author = 'Xiaoxiao.liu'
    author_url = 'https://github.com/x0216u/lark_sentry'
    resource_links = [
        ('Bug Tracker', 'https://github.com/x0216u/lark_sentry/issues'),
        ('Source', 'https://github.com/x0216u/lark_sentry/issues'),
    ]

    conf_key = 'lark_sentry'
    conf_title = title

    project_conf_form = LarkNotificationsOptionsForm

    logger = logging.getLogger('sentry.plugins.lark_sentry')

    def is_configured(self, project, **kwargs):
        return bool(self.get_option('webhook', project) and self.get_option('message_template', project))

    def get_config(self, project, **kwargs):
        return [
            {
                'name': 'webhook',
                'label': 'Webhook',
                'type': 'text',
                'help': 'Read more: https://getfeishu.cn/hc/en-us/articles/360024984973-Use-Bots-in-group-chat',
                'placeholder': 'https://open.feishu.cn/open-apis/bot/hook/xxx',
                'validators': [],
                'required': True,
            },
            {
                'name': 'message_template',
                'label': 'Message Template',
                'type': 'textarea',
                'help': 'Set in standard python\'s {}-format convention, available names are: '
                        'Undefined tags will be shown as [not set], <hr> means underline, <btn:text> means a button',
                'validators': [],
                'required': True,
                'default': "{header} 【项目】{project_name} 【用户】{user} 【环境】{tag['environment']} 【版本】{tag['sentry:release']}"
                           " <hr> 【内容】{message} <btn:text>{url}"
            },
        ]

    def build_message(self, group, event):
        tags = defaultdict(lambda: '[not set]')
        tags.update({k: v for k, v in event.tags})
        names = {
            'header': event.title,
            'tag': tags,
            'message': event.message,
            'project_name': group.project.name,
            'url': group.get_absolute_url(),
        }
        template = self.get_message_template(group.project)

        full_text = template.format(**names)
        full_text_list = full_text.split(' ')

        body = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                }
            }
        }
        elements = []
        if full_text_list:
            body['card']['header'] = {"title": {"tag": "plain_text",
                                                "content": full_text_list.pop(0)}},
            for _div in full_text_list:
                if _div == '<hr>':
                    elements.append({
                        "tag": "hr"
                    })
                elif _div.startswith('<btn:'):
                    btn_arr = _div.split('>')
                    url = btn_arr[-1]
                    btn_text = btn_arr[0].split(':')[-1]
                    elements.append({
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "url": url,
                                "text": {
                                    "tag": "plain_text",
                                    "content": btn_text
                                },
                                "type": "primary"
                            }
                        ]
                    })
                else:
                    elements.append({
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": _div,
                        }
                    })
        body['card']['elements'] = elements
        return body

    def get_message_template(self, project):
        return self.get_option('message_template', project)

    def send_message(self, url, payload):
        self.logger.debug('Sending message to %s ' % url)
        response = safe_urlopen(
            method='POST',
            url=url,
            json=payload,
        )
        self.logger.debug('Response code: %s, content: %s' % (response.status_code, response.content))

    def notify_users(self, group, event, fail_silently=False, **kwargs):
        self.logger.debug('Received notification for event tag: %s' % event.tags)
        payload = self.build_message(group, event)
        self.logger.debug('Built payload: %s' % payload)
        url = self.get_option('webhook', group.project)
        self.logger.debug('Webhook url: %s' % url)
        safe_execute(self.send_message, url, payload, _with_transaction=False)
