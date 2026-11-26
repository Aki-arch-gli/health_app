# 暮らしの食卓

夕食の献立、地域の相談先、従来の健康記録と交流機能をまとめたアプリです。

## 起動方法

Windowsでは「起動.cmd」を開きます。Streamlitなどの依存パッケージが未設定の場合は、初回起動時にインストールします。手動で起動する場合は、このフォルダで次を実行します。

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

「ホーム」「献立」「健康記録」「交流・思い出」「設定」の5つがメインタブです。「ホーム」に生活相談があります。「献立」では、食材から夕食を組み合わせる方法と、従来の朝・昼・夕の献立、週間献立、思い出レシピ投票、冷蔵庫検索、お気に入りが使えます。検索結果には料理の参考写真を表示します。

「献立」→「今日の献立」→「食材から夕食」では、1人1食の予算、安さや野菜の量で候補を選べます。予算の基準を「買い足す食材だけ」にすると、家にある食材を除いて絞り込めます。`data/ingredient_prices.json` の参考単価と、使う食材の分量から費用を計算します。買い足す食材の金額も、使用分の目安です。

同じ画面の利用中は、タブを移っても直前に検索した条件を呼び出せます。「別の献立を探す」は条件を保った候補に入れ替えます。

ログインして保存した夕食は「献立」→「お気に入り」で次回も見返せます。ゲスト中に保存した夕食も、同じ画面でログインした後に「ゲストで保存した夕食を引き継ぐ」を選べます。

「献立」→「外食マップ」では、西東京市と近隣の登録店を距離・予算・料理の種類・野菜料理付きの条件で探せます。結果は近い順または掲載メニューが安い順に並べられます。店とメニュー例は `data/dining_directory.json` に出典と確認日付きで登録しています。現在地を使うにはブラウザーで許可してください。駅名でも検索できます。未登録の地域は外部マップに検索を引き継ぎます。

## ログインと従来のデータ

献立、生活相談、今日のスタンプのお試しは登録なしで使えます。Supabaseを設定していない場合は、アプリが動くPCにアカウントと記録を保存します。既存のSupabase設定を使う場合は、従来のアカウントでログインします。この作業フォルダと元のアプリでは、データの保存先がそれぞれ異なります。

接続には `SUPABASE_URL` と `SUPABASE_KEY` を使います。ログイン保持の設定は `COOKIES_PASSWORD` です。施設職員・家族・管理者の切り替えは、それぞれ `FACILITY_PASSWORD`、`FAMILY_PASSWORD`、`ADMIN_PASSWORD` を使います。設定値は Streamlit の Secrets または環境変数に置きます。

施設職員が担当利用者の記録を扱うには、管理者が確認した組み合わせを Streamlit の Secrets の `[FACILITY_CLIENTS]` に登録します。キーは職員のユーザーID、値は担当利用者のユーザーIDの配列です。担当の登録がない職員は、自分の健康記録を利用できます。

```toml
[FACILITY_CLIENTS]
"staff-example" = ["member-example"]
```

## 毎日の記録と見守り

ホームで気分や食欲、今日の小さな一歩を記録できます。スタンプは日本時間で1日1つです。今日のひとこととスタンプは取り消せます。会員の記録は次にログインしたときも見返せます。健康記録では直近30日から日付を選び、入力した水分・体重・血圧の項目ごとに保存・取り消しできます。

本人が「設定」の「見守りの共有」で招待コードを発行し、相手が自分のアカウントで受け取ったコードを入力します。コードの有効期間は24時間で、使えるのは1回です。相手は「交流・思い出」で共有開始日以降の直近7日分のスタンプを見られます。本人は個々の相手について気分と食欲を共有するか選べます。本人も相手も共有を停止できます。

「設定」で保存したプロフィールは、他の記録と同じアプリの保存先から再ログイン時に読み込みます。写真アルバムは「自分だけ」が初期値です。過去の家族・施設限定投稿は投稿者の画面で確認できます。

## QRコードでの共有

`127.0.0.1` はアプリを起動した機器を指すアドレスです。会場外向けの一時公開では、Streamlitに接続した[Cloudflare Quick Tunnel](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)のHTTPSアドレスから試用リンクとQRコードを作ります。受け取った人は試用コードの入力なしで開けます。リンクとQRコード自体に入場権限があるため、試用参加者のみに配布します。

Windowsのエクスプローラーで「試用版を開始.cmd」をダブルクリックすると、このPCのブラウザーでアプリが開きます。黒いウィンドウに表示されるHTTPSリンクと「試用版QR.png」は参加者向けです。Cloudflareが前の接続を失っている場合は、新しいリンクとQRコードが発行されます。

公開中はこのPCを起動したままインターネットに接続します。「試用版を停止.cmd」で公開を停止できます。Cloudflareの実行ファイルが見つからない場合は、[cloudflaredをインストール](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/)して再度開きます。

試用モードは `KURASHI_TRIAL_MODE=1`、16文字以上のランダムな `KURASHI_TRIAL_CODE`、別の絶対パスを指定する `KURASHI_DATA_DIR` で起動します。同じ試用データフォルダを使えば、公開をやり直しても会員の試用記録は残ります。参加者にはニックネームと架空の健康データで試してもらいます。

## Streamlit Community Cloudでの公開

[Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)では、GitHubに置いたソースコードから `app.py` を公開できます。GitHubに登録するのはコード、依存関係、献立データ、画像素材です。個人の記録、投稿写真、試用QR、接続設定はGitHubの管理対象から除外します。

[Community Cloudのローカルファイルは永続化が保証されません](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data)。アカウントや日々の記録を残す試用を移行する場合は、永続データベースへの接続と、ログイン後に記録を復元できることの確認が必要です。

## 生活相談

相談先は区分と地域から探せます。西東京市では、困りごとが複数ある場合に福祉丸ごと相談窓口を表示します。高齢の方やご家族のことも相談する場合は、担当の地域包括支援センターを町名から確認できます。タブを移っても、開いている間は相談条件とメモを見返せます。相談メモを編集・保存し、利用者から窓口へ電話や面談で伝えます。成人向けのローカル試用でAIを使うには、`ENABLE_LOCAL_CONSULT_AI=true` と `GEMINI_API_KEY` を設定します。選択したテーマと項目だけを、同意後にGeminiへ送ります。

### 地域包括支援センターへの案内と連携の準備

ホームの「地域包括支援センターを探す」から、相談したい方の居住地を選びます。西東京市の8センターは、町名ごとの担当、所在地、開設時間、電話、行き方が分かります。遠方の家族が相談するときも、本人が住む地域で探します。「初めての相談・つながらなかったとき」で、電話で伝えることと別の相談先を確認できます。保存するメモには窓口情報と次の連絡日の記入欄が含まれます。

現在の案内は、市の公開情報をもとに利用者自身が窓口に連絡する方式です。連携を試行する際は、市の高齢者支援課地域支援係や担当センターと、次の点を確認します。

1. 受け付けられる相談の範囲、案内してよい電話・来所・訪問の手順、担当外だった場合の窓口をすり合わせます。
2. 本人の同意を得た紹介を扱う場合は、連絡する担当者、共有する最小限の項目、受け取る方法、連絡がつかない場合の対応を双方で決めます。
3. 試行には架空の相談事例を使い、利用者と職員が迷った箇所を確認します。窓口情報の更新担当と確認時期を決め、受付情報が変わったときに更新します。

[西東京市の地域包括支援センター一覧](https://www.city.nishitokyo.lg.jp/kenko_hukusi/koreisyasien/chiikihoukatu.html)

`index.html` は既存のブラウザー簡易版です。5タブと会員機能を含む統合版は `app.py` から起動します。

## 写真素材

トップの写真は組み込みのImageGenで制作し、[assets/dinner-hero.jpg](assets/dinner-hero.jpg) に収録しています。

> Use case: photorealistic-natural. Asset type: wide homepage hero photo for a Japanese community food and wellbeing app. Create a realistic warm overhead-angled editorial photograph of a Japanese everyday home dinner with a handmade ceramic bowl of steamed white rice, glazed grilled salmon with a small wedge of citrus, a small side bowl of bright green vegetables and sesame, and an ochre cup of miso soup. Oatmeal linen on a light honey oak table, subtle tactile detail and natural late afternoon window light, neutral cream, olive greens, soft browns. Relaxed generously spaced arrangement, honestly home-cooked, compelling food texture, main plate centered, composition must crop gracefully to a 3:2 card and to 16:9. Cozy Japanese cookbook photography, no restaurant plating, hands, people, letters, logos or watermark.

ホームの食卓イラストも組み込みのImageGenで制作し、[assets/dinner-illustration.jpg](assets/dinner-illustration.jpg) に収録しています。

> Use case: illustration-story. Asset type: wide header artwork for a Japanese community dinner planner. Draw an original slice-of-life anime-style illustration, an overhead view of an everyday Japanese bento tray with rice, a piece of grilled salmon, a side portion of leafy greens, and a small cup of soup. A little folded cloth and chopsticks on a pale warm cream kitchen table. Clean hand-drawn dark green outlines, flat gouache-like colors with gentle paper texture, a few restrained mustard yellow and persimmon accents. Friendly, legible shapes and a mostly flat two-tone background. Compact composition, meal fully visible, 3:2 landscape crop. Warm grown-up illustration for a local community newsletter. No gradient, 3D render, photographic detail, human figures, letters, logo or watermark.
