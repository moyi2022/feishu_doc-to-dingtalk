# -*- coding: utf-8 -*-
"""
钉钉 unionId 获取工具

使用方法：
1. 确保已开通以下权限：
   - 通讯录只读权限 (qyapi_get_member)
   - 通过手机号获取用户信息 (qyapi_get_member_by_mobile)

2. 运行此脚本：
   python get_unionid.py

3. 按提示输入信息
"""

import requests
import sys


def get_access_token(corp_id: str, client_id: str, client_secret: str) -> str:
    """获取钉钉 access_token"""
    url = f'https://api.dingtalk.com/v1.0/oauth2/{corp_id}/token'
    response = requests.post(url, json={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    })

    if response.status_code != 200:
        raise Exception(f"获取 token 失败: {response.text}")

    return response.json().get('access_token')


def get_unionid_by_userid(token: str, user_id: str) -> dict:
    """通过 userId 获取用户信息（包含 unionId）"""
    url = f'https://oapi.dingtalk.com/topapi/v2/user/get?access_token={token}'
    response = requests.post(url, json={'userid': user_id})

    data = response.json()
    if data.get('errcode') != 0:
        raise Exception(f"获取用户信息失败: {data.get('errmsg')}")

    result = data.get('result', {})
    return {
        'userid': result.get('userid'),
        'unionid': result.get('unionid'),
        'name': result.get('name'),
        'mobile': result.get('mobile')
    }


def get_userid_by_mobile(token: str, mobile: str) -> str:
    """通过手机号获取 userId"""
    url = f'https://oapi.dingtalk.com/topapi/v2/user/getbymobile?access_token={token}'
    response = requests.post(url, json={'mobile': mobile})

    data = response.json()
    if data.get('errcode') != 0:
        raise Exception(f"通过手机号获取用户失败: {data.get('errmsg')}")

    return data.get('result', {}).get('userid')


def main():
    print("=" * 60)
    print("钉钉 unionId 获取工具")
    print("=" * 60)

    print("\n【所需权限】")
    print("在钉钉开放平台 → 应用 → 权限管理 中开通：")
    print("  ✓ 通讯录只读权限 (Contact.User.Read)")
    print("  ✓ 通过手机号获取用户信息 (qyapi_get_member_by_mobile)")
    print("  ✓ 成员信息读权限 (qyapi_get_member)")

    print("\n" + "-" * 60)

    # 输入凭证
    print("\n请输入钉钉应用凭证：")
    corp_id = input("Corp ID (企业ID): ").strip()
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()

    if not all([corp_id, client_id, client_secret]):
        print("\n错误：凭证不能为空")
        return

    try:
        # 获取 token
        print("\n[1] 获取 access_token...")
        token = get_access_token(corp_id, client_id, client_secret)
        print(f"    成功: {token[:20]}...")

        # 选择获取方式
        print("\n" + "-" * 60)
        print("选择获取方式：")
        print("  1. 通过 userId 获取（如果你知道用户的 userId）")
        print("  2. 通过手机号获取（如果你知道用户的手机号）")

        choice = input("\n请选择 (1/2): ").strip()

        if choice == '1':
            user_id = input("请输入 userId: ").strip()
            if not user_id:
                print("错误：userId 不能为空")
                return

            print("\n[2] 获取用户信息...")
            user_info = get_unionid_by_userid(token, user_id)

        elif choice == '2':
            mobile = input("请输入手机号: ").strip()
            if not mobile:
                print("错误：手机号不能为空")
                return

            print("\n[2] 通过手机号获取 userId...")
            user_id = get_userid_by_mobile(token, mobile)
            print(f"    userId: {user_id}")

            print("\n[3] 获取用户信息...")
            user_info = get_unionid_by_userid(token, user_id)

        else:
            print("无效选择")
            return

        # 输出结果
        print("\n" + "=" * 60)
        print("获取成功！")
        print("=" * 60)
        print(f"用户名: {user_info.get('name')}")
        print(f"手机号: {user_info.get('mobile')}")
        print(f"userId: {user_info.get('userid')}")
        print(f"unionId: {user_info.get('unionid')}")
        print("=" * 60)
        print("\n请将上面的 unionId 用于文档迁移工具！")

    except Exception as e:
        print(f"\n错误: {str(e)}")
        if "60011" in str(e):
            print("\n提示：权限不足，请在钉钉开放平台开通相关权限")


if __name__ == '__main__':
    main()