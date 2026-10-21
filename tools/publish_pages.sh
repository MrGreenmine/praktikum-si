#!/bin/sh
# Пересобирает сайт и обновляет ветку gh-pages, из которой публикуется GitHub Pages.
#
#   sh tools/publish_pages.sh
#
# Требуется, чтобы в репозитории был настроен remote origin и были доступны
# учётные данные для push (PAT или SSH-ключ).
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Сборка сайта в site/"
python3 tools/build.py "$ROOT/site"

echo "==> Формируем содержимое ветки gh-pages"
# Дерево собирается прямо из содержимого site/ (в корне ветки, без префикса site/),
# рабочее дерево репозитория не трогаем.
TMPINDEX="$(mktemp)"
rm -f "$TMPINDEX"
TMPTREE="$(mktemp -d)"
cp -R site/. "$TMPTREE/"
export GIT_INDEX_FILE="$TMPINDEX"
export GIT_DIR="$ROOT/.git"
export GIT_WORK_TREE="$TMPTREE"
git read-tree --empty
( cd "$TMPTREE" && git add -A . )
TREE="$(git write-tree)"
COMMIT="$(git commit-tree "$TREE" -m "Обновление сайта (автопубликация)")"
unset GIT_INDEX_FILE
unset GIT_DIR
unset GIT_WORK_TREE
rm -f "$TMPINDEX"
rm -rf "$TMPTREE"

git branch -f gh-pages "$COMMIT"

echo "==> Публикуем ветку gh-pages"
git push --force origin gh-pages:gh-pages

echo
echo "Готово. Включить GitHub Pages:"
echo "  Settings -> Pages -> Source: Deploy from a branch"
echo "  branch: gh-pages, folder: / (root) -> Save"
