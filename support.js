const centersSource = 'https://www.city.nishitokyo.lg.jp/kenko_hukusi/koreisyasien/chiikihoukatu.html';
const nationalCenters = 'https://www.kaigokensaku.mhlw.go.jp/';
const nationalLiving = 'https://www.mhlw.go.jp/stf/newpage_08152.html';
const mentalHealthSource = 'https://www.mhlw.go.jp/mamorouyokokoro/soudan/';

const centers = [
  ['栄町', '042-438-7090', 'sakehoukatu', 'ひばりが丘北・北町・栄町・下保谷'],
  ['富士町', '042-451-1203', 'fujimatihoukatu', '東町・中町・富士町'],
  ['泉町', '042-424-1200', 'izumihoukatu', '北原町・泉町・住吉町'],
  ['田無町', '042-467-8850', 'tanasihoukatu', '田無町・保谷町'],
  ['緑町', '042-461-7081', 'midorihoukatu', '緑町・谷戸町・ひばりが丘'],
  ['西原町', '042-451-8844', 'nisiharahoukatu', '西原町・芝久保町'],
  ['向台町', '042-468-2340', 'mukoudaihoukatu', '南町・向台町'],
  ['新町', '042-462-1695', 'sinmatihoukatu', '新町・柳沢・東伏見'],
].map(([name, phone, slug, area]) => ({
  title: `${name}地域包括支援センター`,
  phones: [[phone, '']],
  area: area.split('・'),
  url: `https://www.city.nishitokyo.lg.jp/sisetu/hukusi/${slug}.html`,
  link: '市公式ページで受付時間を見る',
}));

const localLiving = {
  title: '西東京市 生活サポート相談窓口',
  description: '食費や家計、仕事など、生活の困りごとを相談できます。',
  phones: [['042-420-2809', '田無庁舎'], ['042-438-4023', '保谷庁舎']],
  url: 'https://www.city.nishitokyo.lg.jp/kenko_hukusi/seikatuenzyo/seikatukonkyuusha.html',
};
const localNutrition = {
  title: '西東京市 栄養・食生活相談',
  description: '管理栄養士が食生活の相談を受け付けています。電話で申し込みます。',
  phones: [['042-439-3526', '健康課']],
  url: 'https://www.city.nishitokyo.lg.jp/kenko_hukusi/seizinhoken/sodan/eiyousoudan.html',
};
const mentalHealth = {
  title: 'こころの相談窓口',
  description: '気持ちのつらさや孤立について、電話やSNSなど、話しやすい方法で探せます。',
  url: mentalHealthSource,
  link: '厚生労働省の一覧を開く',
};

const topics = {
  money: {
    label: '食費・生活費',
    options: ['食費が足りない', '日々の支払いが心配', '支援の利用方法を知りたい'],
    firstQuestion: 'どんな支援や相談を利用できますか',
  },
  shopping: {
    label: '買い物・食事の用意',
    options: ['買い物に行くのが難しい', '調理の負担が大きい', '配食などを知りたい'],
    firstQuestion: '買い物や食事の用意を助けるサービスはありますか',
  },
  care: {
    label: '介護・高齢の家族',
    options: ['家族の介護に負担を感じる', '離れて暮らす家族が心配', '誰に相談するか迷っている'],
    firstQuestion: '本人や家族が受けられる支援には何がありますか',
  },
  nutrition: {
    label: '栄養・食生活',
    options: ['食事の量や組み合わせが気になる', '食事について専門職に聞きたい', '食事の用意を続けるのが難しい'],
    firstQuestion: '食事について管理栄養士などに相談できますか',
  },
  feelings: {
    label: '気持ち・孤立',
    options: ['気持ちの負担が大きい', '話せる相手が少ない', '相談のきっかけを探している'],
    firstQuestion: '話しやすい相談方法や地域の居場所はありますか',
  },
};

const followupQuestions = {
  first: '最初にどこへ、どのように相談すればよいですか',
  bring: '最初の相談までに準備するものはありますか',
  fee: '利用できるサービスの費用や対象条件を教えてもらえますか',
  family: '家族からでも相談できますか',
  visit: '外出が難しい場合に利用できる相談方法はありますか',
  privacy: '相談した内容は、どの範囲で共有されますか',
};

function supportContacts(topic, local, town, forOlder) {
  const center = centers.find((entry) => entry.area.includes(town));
  const localCenter = center ? {
    ...center,
    description: `担当地区は${center.area.join('・')}です。`,
  } : {
    title: '西東京市 地域包括支援センター',
    description: '町名ごとの担当窓口を確認できます。担当が分からないときは市の高齢者支援課に相談できます。',
    phones: [['042-420-2811', '高齢者支援課']],
    url: centersSource,
    link: '担当地区一覧を開く',
  };
  const nearbyCenter = local ? localCenter : {
    title: 'お住まいの地域の地域包括支援センター',
    description: '高齢の本人や家族の介護・見守り・生活の相談先を住所から探せます。',
    url: nationalCenters,
    link: '厚生労働省の介護サービス情報公表システムを開く',
  };
  const living = local ? localLiving : {
    title: 'お住まいの地域の自立相談支援機関',
    description: 'お住まいの市区町村に、食費や生活費について相談できる窓口を確認できます。',
    url: nationalLiving,
    link: '厚生労働省の制度案内を開く',
  };
  if (topic === 'care') return [nearbyCenter];
  if (topic === 'shopping' && forOlder) return local ? [nearbyCenter, {
    title: '西東京市 高齢者見守り配食サービス',
    description: '食事の用意や安否確認に支援が必要な方へ。対象要件と申し込み先を市のページで確認できます。',
    url: 'https://www.city.nishitokyo.lg.jp/kenko_hukusi/koreisyasien/kaigo_dailylife/haisyoku202107.html',
  }] : [nearbyCenter];
  if (topic === 'nutrition') return [local ? localNutrition : {
    title: '市区町村の保健センター・栄養相談',
    description: '自治体のサイトや電話窓口で「栄養相談」「食生活相談」とお尋ねください。',
  }];
  if (topic === 'feelings') return [mentalHealth];
  return [living];
}
