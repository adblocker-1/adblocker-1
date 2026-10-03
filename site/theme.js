/* Tag/Nacht-Umschalter. Die gespeicherte Wahl setzt bereits ein kleines
   Inline-Skript im <head>, damit beim Laden nichts aufblitzt. */
(function () {
  var root = document.documentElement;
  var btn = document.querySelector(".theme");
  function label() {
    var dark = root.dataset.theme === "dark";
    btn.innerHTML = dark ? '<span lang="ja">昼</span>Tag' : '<span lang="ja">夜</span>Nacht';
    btn.setAttribute("aria-label", dark ? "Zur Tag-Ansicht wechseln" : "Zur Nacht-Ansicht wechseln");
    document.querySelector('meta[name="theme-color"]').content = dark ? "#0B1220" : "#FBF7EF";
  }
  btn.addEventListener("click", function () {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
    label();
  });
  label();
})();
