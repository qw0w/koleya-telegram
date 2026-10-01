# Колея — Telegram Mini App build

Эта папка — отдельная Telegram-версия игры. Исходная Yandex-версия не изменялась.

## Что уже сделано

- подключён официальный Telegram Mini Apps JS SDK;
- игра сообщает Telegram `ready()`, расширяет viewport и best-effort запрашивает fullscreen;
- учитываются Telegram safe-area inset в полноэкранном режиме;
- отключены вертикальные свайпы Telegram там, где API это поддерживает;
- язык берётся из Telegram user.language_code с fallback на язык браузера;
- Yandex Ads заменены единым адаптером AdsGram;
- все существующие вызовы `sdk.rewarded(...)` теперь готовы к AdsGram Rewarded;
- `sdk.fullscreen(...)` готов к отдельному AdsGram Interstitial block, но по умолчанию выключен;
- сохранения работают через localStorage и разделяются по Telegram user id, если Mini App запущен внутри Telegram;
- добавлен `.nojekyll` для GitHub Pages.

## 1. Сначала проверь игру на GitHub Pages

Создай пустой GitHub repository и загрузи **содержимое этой папки** в корень репозитория:

- `index.html`
- `telegram-config.js`
- `.nojekyll`
- `fonts/`

В GitHub: Settings → Pages → Deploy from a branch → `main` / `(root)`.
После публикации получится HTTPS URL вида:

`https://USERNAME.github.io/REPOSITORY/`

## 2. Подключи Mini App к Telegram

В BotFather создай/выбери бота и укажи HTTPS URL GitHub Pages как URL Mini App.

## 3. Подключи Rewarded Ads

В AdsGram создай Rewarded block для Mini App. После модерации вставь его ID в `telegram-config.js`:

```js
window.KOLEYA_TG_CONFIG = {
  rewardBlockId: "ТВОЙ_BLOCK_ID",
  interstitialBlockId: "",
  useInterstitial: false,
  requestFullscreen: true,
  devRewardWithoutAd: false
};
```

В игре уже есть существующие rewarded-точки. Награда выдаётся только если `AdController.show()` успешно завершился.

## 4. Interstitial (необязательно)

Для полноэкранной рекламы создай отдельный Interstitial block и впиши ID в `interstitialBlockId`, затем поставь `useInterstitial: true`.
На первом релизе лучше оставить `false` и проверить удержание на Rewarded Ads.

## Важно про сохранения

Эта первая статическая сборка хранит прогресс локально на устройстве. Для синхронизации между телефонами нужен backend. На backend необходимо валидировать `Telegram.WebApp.initData` перед тем, как доверять Telegram user id.

## Безопасное тестирование Rewarded UI

По умолчанию, если AdsGram ещё не настроен, рекламная кнопка НЕ выдаёт награду.
Если нужно проверить только UI до получения block ID:

1. временно поставь `devRewardWithoutAd: true`;
2. открой URL с `?devads=1`;
3. после проверки верни `devRewardWithoutAd: false`.

Не оставляй dev-режим включённым в релизе.
