import streamlit as st
import requests

# --- 页面设置 ---
st.set_page_config(page_title="Shopify Token 可视化工具", page_icon="🔑", layout="wide")

# --- 初始化 session_state 默认值 ---
if "client_id" not in st.session_state:
    st.session_state.client_id = ""
if "client_secret" not in st.session_state:
    st.session_state.client_secret = ""
if "scopes_str" not in st.session_state:
    st.session_state.scopes_str = "read_products,read_files,write_files"
if "redirect_uri" not in st.session_state:
    st.session_state.redirect_uri = "https://harvey-shopify-access-token-obtainer.streamlit.app"

# 辅助函数：获取清理后的 scopes（去除多余空格，过滤空项）
def get_clean_scopes():
    raw = st.session_state.scopes_str
    if not raw:
        return ""
    parts = [s.strip() for s in raw.split(",") if s.strip()]
    return ",".join(parts)

# --- 侧边栏：App 配置可视化 ---
with st.sidebar:
    st.header("⚙️ Shopify App 配置")
    st.info("请先在此处填写您在 Shopify Partner 后台创建的 App 信息")

    client_id = st.text_input(
        "CLIENT_ID",
        value=st.session_state.client_id,
        placeholder="例如: 0c81a35bb3...",
        key="client_id"
    )
    client_secret = st.text_input(
        "CLIENT_SECRET",
        type="password",
        value=st.session_state.client_secret,
        placeholder="例如: shpss_bd28...",
        key="client_secret"
    )

    # 文本输入框，用户自行输入 scopes（逗号分隔）
    st.text_input(
        "权限范围 (SCOPES) 用逗号分隔",
        value=st.session_state.scopes_str,
        placeholder="例如: read_products,write_products,read_files",
        key="scopes_str",
        help="多个权限用英文逗号分隔，可以加空格，系统自动清理"
    )

    redirect_uri = st.text_input(
        "REDIRECT_URI",
        value=st.session_state.redirect_uri,
        key="redirect_uri"
    )

    st.divider()
    st.caption("注：请确保上述 REDIRECT_URI 已填入 Shopify App 后台的 'Allowed redirection URL' 中。")

# --- 主界面逻辑 ---
st.title("🛍️ Shopify Access Token 获取器")

# 获取 URL 中的参数
query_params = st.query_params

# 检查是否存在回调参数
if "code" in query_params and "shop" in query_params:
    # --- 流程 2：授权回调后的 Token 交换 ---
    shop = query_params["shop"]
    code = query_params["code"]

    st.success(f"✅ 已获取授权码 (Code) 来自店铺: `{shop}`")

    col1, col2 = st.columns(2)
    with col1:
        st.write("**当前使用的换取配置：**")
        st.json({
            "Shop": shop,
            "Client ID": client_id[:5] + "******" if client_id else "",
            "Scopes": get_clean_scopes()  # 显示清理后的 scopes
        })

    if st.button("🔥 立即兑换 Access Token", type="primary"):
        if not client_id or not client_secret:
            st.error("❌ 错误：侧边栏的 Client ID 或 Secret 不能为空！")
        else:
            with st.spinner("正在向 Shopify 交换令牌..."):
                access_token_url = f"https://{shop}/admin/oauth/access_token"
                payload = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code
                }
                try:
                    res = requests.post(access_token_url, json=payload)
                    data = res.json()

                    if "access_token" in data:
                        st.balloons()
                        st.subheader("🎉 获取成功！")
                        st.info("您的 Access Token 如下：")
                        st.code(data["access_token"], language="text")
                        st.warning("⚠️ 请立即保存，刷新页面后此信息将消失。")
                    else:
                        st.error("交换失败")
                        st.json(data)
                except Exception as e:
                    st.error(f"网络异常: {e}")

    if st.button("↩️ 返回重新开始"):
        st.query_params.clear()
        st.rerun()

else:
    # --- 流程 1：输入店铺发起授权 ---
    st.markdown("### 第一步：发起授权")

    container = st.container(border=True)
    with container:
        shop_url = st.text_input("输入店铺域名:", placeholder="my-shop.myshopify.com")

        if st.button("🚀 生成授权链接并跳转", type="primary"):
            if not client_id or not shop_url:
                st.warning("⚠️ 请确保侧边栏的 Client ID 和主页面的店铺域名已填写。")
            else:
                # 自动补全域名
                full_shop_url = shop_url if ".myshopify.com" in shop_url else f"{shop_url}.myshopify.com"

                # 构建授权 URL，使用清理后的 scopes
                clean_scopes = get_clean_scopes()
                auth_url = (
                    f"https://{full_shop_url}/admin/oauth/authorize?"
                    f"client_id={client_id}&"
                    f"scope={clean_scopes}&"
                    f"redirect_uri={redirect_uri}"
                )

                st.write("---")
                st.write("🔗 **授权链接已生成：**")
                st.link_button("👉 点击进入 Shopify 授权界面", auth_url)
                st.caption("点击后在新窗口完成授权，Shopify 会自动跳回此页面。")

# --- 帮助说明 ---
with st.expander("ℹ️ 使用帮助"):
    st.markdown("""
    1. **Shopify 后台配置**: 登录 [Shopify Partner Dashboard](https://partners.shopify.com/)。
    2. **创建 App**: 在 Apps 菜单下创建一个 App。
    3. **设置 Redirect**: 在 App Setup 页面，将本程序的地址填入 **Allowed redirection URL**。
    4. **复制密钥**: 将 API Key (Client ID) 和 Secret 填入本工具左侧边栏。
    5. **输入权限**: 在侧边栏的 **权限范围** 框中输入需要的权限（用英文逗号分隔），例如 `read_products,write_products`。
    6. **开始**: 输入店铺名点击授权即可。
    """)
