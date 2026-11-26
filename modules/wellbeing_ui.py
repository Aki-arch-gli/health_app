from datetime import datetime, timedelta, timezone
from functools import partial

import pandas as pd
import streamlit as st

from modules import wellbeing as store
from modules.meal_print import build_meal_card


def account_id():
    return st.session_state.get("wellbeing_id") if st.session_state.get("is_logged_in") else None


def _week(days, today):
    week = store.week_summary(days, today)
    count = sum(marked for _, marked in week)
    st.markdown(f"**最近7日で {count} 日記録**")
    tiles = []
    for day, marked in week:
        text = "記録あり" if marked else "記録なし"
        icon = "🌱" if marked else "・"
        tiles.append(f'<li aria-label="{day.month}月{day.day}日 {text}"><time datetime="{day}">{day.month}/{day.day}</time><span aria-hidden="true">{icon}</span></li>')
    st.html('<ul class="kurashi-stamps" aria-label="直近7日分のスタンプ">' + "".join(tiles) + '</ul>')


def render_today(open_login):
    today = store.today_in_japan()
    owner = account_id()
    if owner:
        days = store.own_days(owner, today)
    else:
        demo = st.session_state.get("guest_wellbeing_day")
        days = [demo] if demo and demo[0] == today.isoformat() else []
    latest = next((row for row in days if row[0] == today.isoformat()), None)
    mood, appetite, stepped = latest[1:] if latest else (None, None, False)
    task = store.STEPS[today.toordinal() % len(store.STEPS)]
    with st.container(key="wellbeing_checkin", border=True):
        st.subheader("今日のひとこと", anchor="today-check-in")
        st.caption(f"{today.month}月{today.day}日　書けるところだけ選べます。")
        if not owner:
            st.caption("ゲストのスタンプは今の画面を開いている間に楽しめます。")
        with st.form(f"wellbeing_today_{today.isoformat()}_{latest is not None}"):
            left, right = st.columns(2)
            mood = left.segmented_control("今日の気分", store.MOODS, default=mood)
            appetite = right.segmented_control("今日の食欲", store.APPETITES, default=appetite)
            st.write(f"**今日の小さな一歩**　{task}")
            stepped = st.checkbox("できた", value=bool(stepped))
            save = st.form_submit_button("今日の記録を更新" if latest else "今日のスタンプを押す", type="primary")
        if save:
            if owner:
                store.save_day(owner, today, mood, appetite, stepped)
            else:
                st.session_state.guest_wellbeing_day = (today.isoformat(), mood, appetite, stepped)
            st.session_state.wellbeing_saved = "今日の記録を更新しました。" if latest else "今日のスタンプが増えました。"
            st.rerun()
        notice = st.session_state.pop("wellbeing_saved", None)
        if notice:
            st.success(notice)
        _week(days, today)
        if latest:
            with st.popover("今日の記録を取り消す"):
                if st.button("今日のひとこととスタンプを取り消す", key="clear_today_stamp"):
                    if owner:
                        store.clear_day(owner, today)
                    else:
                        st.session_state.pop("guest_wellbeing_day", None)
                    st.session_state.wellbeing_saved = "今日のひとこととスタンプを取り消しました。"
                    st.rerun()
        if owner:
            number = len(days)
            stage = "種" if number < 3 else "芽" if number < 7 else "若葉" if number < 14 else "花"
            st.caption(f"食卓の鉢　{stage} · これまでに {number} 日記録。休んだ日があっても、いつでも続きから。")
            guest = st.session_state.get("guest_wellbeing_day")
            if guest and not latest and guest[0] == today.isoformat():
                if st.button("ゲストで試した今日の記録を引き継ぐ", key="wellbeing_import_guest"):
                    store.save_day(owner, today, *guest[1:])
                    st.session_state.pop("guest_wellbeing_day", None)
                    st.rerun()
            if any(row[1] or row[2] for row in days):
                with st.expander("自分の記録を見返す"):
                    data = [(day, value or "—", food or "—") for day, value, food, _ in days[:7]]
                    st.dataframe(pd.DataFrame(data, columns=["日付", "気分", "食欲"]), hide_index=True)
        elif st.button("アカウントを使って毎日の記録を残す", key="wellbeing_login"):
            open_login()


def render_watch_settings():
    owner = account_id()
    if not owner:
        return
    now = datetime.now(timezone.utc)
    name = st.session_state.get("wellbeing_display_name") or st.session_state.user_id
    st.subheader("見守りの共有")
    st.write("共有先は、共有開始日以降の直近7日分のスタンプを閲覧し、あなたにメッセージを送れます。")
    st.caption("気分と食欲は下で選んだ場合に共有されます。水分・体重・血圧は本人の記録に表示されます。")
    st.caption("共有先は表示された内容をPDFで保存できます。保存済みのPDFは共有先の端末に残ります。")
    details = st.checkbox("気分と食欲も共有する", key="wellbeing_invite_details")
    if st.button("招待コードを発行", key="wellbeing_issue"):
        st.session_state.wellbeing_invite_code = store.create_invite(owner, name, details, now)
    if store.invite_pending(owner, now):
        code = st.session_state.get("wellbeing_invite_code")
        if code and store.invite_pending(owner, now, code):
            st.code(code, language=None)
        st.caption("招待コードは24時間以内に1回使えます。渡す相手を選んでください。")
        if st.button("この招待を取り消す", key="wellbeing_cancel_invite"):
            store.cancel_invite(owner)
            st.session_state.pop("wellbeing_invite_code", None)
            st.rerun()
    st.write("**共有している相手**")
    shares = store.outgoing_shares(owner)
    if not shares:
        st.caption("共有中の相手はいません。")
    for viewer, viewer_name, share_details in shares:
        row, action = st.columns([3, 2], vertical_alignment="center")
        row.text(f"{viewer_name} · {'スタンプ、気分、食欲' if share_details else 'スタンプ'}")
        with action.popover("共有を変更"):
            if share_details and st.button("スタンプだけに変更", key=f"wellbeing_limit_{viewer}"):
                store.limit_share_to_stamps(owner, viewer)
                st.rerun()
            if st.button("この相手との共有を停止", key=f"wellbeing_revoke_{viewer}"):
                store.revoke_share(owner, viewer)
                st.rerun()
    with st.form("wellbeing_accept_invite", clear_on_submit=True):
        invite = st.text_input("受け取った招待コード", type="password", max_chars=24)
        if st.form_submit_button("見守りを始める", key="wellbeing_accept"):
            if store.redeem_invite(invite, owner, name, now):
                st.success("登録しました。「交流・思い出」の見守りから記録を確認できます。")
            else:
                st.warning("招待コードを確認してください。期限切れや使用済みの場合は、本人に再発行を頼めます。")


def _shared_week_pdf(viewer, owner):
    current = store.shared_weeks(viewer, store.today_in_japan()).get(owner)
    if not current or not current["days"]:
        return build_meal_card("共有された見守り記録", [("現在の共有内容", ["表示できる記録はありません。"])])
    lines = []
    for day, mood, appetite in current["days"]:
        text = f"気分 {mood or '—'}　食欲 {appetite or '—'}" if current["details"] else "記録あり"
        lines.append(f"{day}　{text}")
    return build_meal_card("共有された見守り記録", [(current["name"], lines)])


def render_shared():
    viewer = account_id()
    if not viewer:
        return
    today = store.today_in_japan()
    st.subheader("共有された見守り記録")
    shared = store.shared_weeks(viewer, today)
    if not shared:
        st.caption("本人から招待を受け取ったら、設定の「見守りの共有」から登録できます。")
        return
    st.caption("本人が記録した日を表示します。記録が空いている日も、本人の状態はこの画面ではわかりません。")
    for owner, entry in shared.items():
        with st.container(border=True):
            st.text(entry["name"])
            days = entry["days"]
            _week(days, today)
            if days and entry["details"]:
                for day, mood, appetite in days:
                    st.text(f"{day}　気分 {mood or '—'}　食欲 {appetite or '—'}")
            if days:
                st.download_button("共有記録をPDF保存", partial(_shared_week_pdf, viewer, owner),
                                   file_name="wellbeing-week.pdf", mime="application/pdf",
                                   key=f"shared_pdf_{owner}", on_click="ignore")
            with st.form(f"wellbeing_note_{owner}", clear_on_submit=True):
                message = st.text_input("ひとこと送る", max_chars=250, placeholder="例　今日も応援しています")
                if st.form_submit_button("メッセージを送る"):
                    if store.send_message(viewer, owner, message):
                        st.success("メッセージを送りました。")
                    else:
                        st.warning("メッセージを入力し、共有中であることを確認してください。")
            with st.popover("この方の見守りをやめる"):
                st.caption("再開する場合は、本人に招待コードを発行してもらいます。")
                if st.button("見守りを終了する", key=f"wellbeing_leave_{owner}"):
                    store.revoke_share(owner, viewer)
                    st.rerun()


def render_messages():
    owner = account_id()
    if not owner:
        return
    msgs = store.recent_messages(owner)
    if msgs:
        st.subheader("届いたひとこと")
    for sent_at, sender, body in msgs:
        local = datetime.fromisoformat(sent_at).astimezone(store.TOKYO)
        with st.container(border=True):
            st.caption(f"{local:%m/%d}　{sender}")
            st.text(body)


def render_measurements():
    owner = account_id()
    if not owner:
        return
    today = store.today_in_japan()
    current = store.measure_rows(owner, today, 1)
    water = current[0][1] if current else None
    st.subheader("今日の水分記録")
    st.write("まだ記録がありません。" if water is None else f"今日の記録　**{water:,} mL**")
    with st.container(horizontal=True):
        for label, amount in (("水 200 mL", 200), ("お茶 150 mL", 150), ("汁物 150 mL", 150), ("飲み物 500 mL", 500)):
            if st.button(label, key=f"wellbeing_water_{label}"):
                store.record_water(owner, today, amount)
                st.rerun()
    with st.expander("水分・体重・血圧を入力・修正する"):
        record_day = st.date_input(
            "記録する日", value=today, min_value=today - timedelta(days=29), max_value=today, key="measure_day",
        )
        rows_for_day = current if record_day == today else store.measure_rows(owner, record_day, 1)
        water, weight, high, low = rows_for_day[0][1:] if rows_for_day else (None, None, None, None)
        st.caption("選んだ日の記録です。入力した項目だけを更新します。")
        if water is not None:
            st.caption(f"保存済みの水分量　{water:,} mL")
        if weight is not None:
            st.caption(f"保存済みの体重　{weight:g} kg")
        if high is not None or low is not None:
            high_label = high if high is not None else "未入力"
            low_label = low if low is not None else "未入力"
            st.caption(f"保存済みの血圧　上 {high_label} ／ 下 {low_label} mmHg")
        with st.form(f"wellbeing_measures_{record_day.isoformat()}"):
            a, b = st.columns(2)
            water_input = a.number_input("その日の水分量 (mL)", min_value=0, step=50, value=None, placeholder="未入力")
            weight_input = b.number_input("体重 (kg)", min_value=0.1, step=0.1, value=None, placeholder="未入力")
            high_input = a.number_input("上の血圧 (mmHg)", min_value=1, step=1, value=None, placeholder="未入力")
            low_input = b.number_input("下の血圧 (mmHg)", min_value=1, step=1, value=None, placeholder="未入力")
            if st.form_submit_button("測定値を保存", key="wellbeing_save_measures"):
                if all(value is None for value in (water_input, weight_input, high_input, low_input)):
                    st.info("記録したい項目を入力してください。")
                else:
                    try:
                        store.save_measures(owner, record_day, water_input, weight_input, high_input, low_input)
                    except ValueError as error:
                        st.warning(str(error))
                    else:
                        st.session_state.measure_notice = f"{record_day.month}月{record_day.day}日の測定値を保存しました。"
                        st.rerun()
    existing = []
    if water is not None:
        existing.append("水分")
    if weight is not None:
        existing.append("体重")
    if high is not None or low is not None:
        existing.append("血圧")
    if existing:
        with st.expander(f"{record_day.month}月{record_day.day}日の記録を取り消す"):
            kind_to_remove = st.selectbox("取り消す項目", existing, index=None, placeholder="項目を選ぶ",
                                          key=f"wellbeing_remove_{record_day.isoformat()}")
            if st.button("選んだ項目を取り消す", disabled=kind_to_remove is None):
                store.clear_measure(owner, record_day, kind_to_remove)
                st.session_state.measure_notice = f"{record_day.month}月{record_day.day}日の{kind_to_remove}の記録を取り消しました。"
                st.rerun()
    if notice := st.session_state.pop("measure_notice", None):
        st.success(notice)
    st.subheader("測定値の推移")
    labels = {"水分": ["水分 (mL)"], "体重": ["体重 (kg)"], "血圧": ["上の血圧", "下の血圧"]}
    kind = st.segmented_control("表示する項目", list(labels), required=True, default="水分", key="wellbeing_measure_kind")
    period = st.segmented_control("期間", ["7日", "30日"], required=True, default="7日")
    rows = store.measure_rows(owner, today, 7 if period == "7日" else 30)
    names = ["日付", "水分 (mL)", "体重 (kg)", "上の血圧", "下の血圧"]
    chart = pd.DataFrame(rows, columns=names).loc[:, ["日付", *labels[kind]]].dropna(how="all", subset=labels[kind])
    if chart.empty:
        st.info("この期間に選んだ項目の記録はありません。")
    else:
        chart["日付"] = pd.to_datetime(chart["日付"])
        if len(chart) == 1:
            st.scatter_chart(chart, x="日付", y=labels[kind], alt=f"{kind}の測定値")
        else:
            st.line_chart(chart, x="日付", y=labels[kind], alt=f"{kind}の測定値の推移")
        chart["日付"] = chart["日付"].dt.strftime("%Y-%m-%d")
        st.dataframe(chart, hide_index=True)
