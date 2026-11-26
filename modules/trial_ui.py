import hashlib
import hmac
import os
import secrets

import streamlit as st

from modules.kurashi_ui import apply_theme, brand
from modules.runtime_paths import trial_directory_ready


def trial_link_token(invite):
    return hmac.new(invite.encode(), b"kurashi-trial-link-v1", "sha256").hexdigest()[:32]


def require_trial_invitation():
    invite = os.getenv("KURASHI_TRIAL_CODE", "")
    if len(invite) < 16 or not trial_directory_ready():
        st.error("試用版の設定を確認しています。準備が整うまでお待ちください。")
        st.stop()

    digest = hashlib.sha256(invite.encode()).hexdigest()
    if "join" in st.query_params:
        tokens = st.query_params.get_all("join")
        del st.query_params["join"]
        if len(tokens) == 1 and secrets.compare_digest(tokens[0].encode(), trial_link_token(invite).encode()):
            st.session_state.trial_admission = digest

    if st.session_state.get("trial_admission") == digest:
        return

    apply_theme()
    brand()
    st.title("暮らしの食卓の試用版")
    st.write("配布されたリンクやQRコードからそのまま開けます。試用コードをお持ちの場合は、下の欄に入力してください。")
    st.caption("試用の記録は運営者のPCに保存されます。ニックネームと架空の健康データでお試しください。")
    with st.form("trial_entry", clear_on_submit=True):
        code = st.text_input("試用コード", type="password", max_chars=128)
        if st.form_submit_button("試用版を開く", type="primary"):
            if secrets.compare_digest(code.strip().encode(), invite.encode()):
                st.session_state.trial_admission = digest
                st.rerun()
            st.error("案内された試用コードを確認してください。")
    st.stop()
