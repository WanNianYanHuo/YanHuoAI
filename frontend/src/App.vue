<template>
  <div class="app-root">
    <router-view />
  </div>
</template>

<style>
:root {
  --bg-color: #000000;
  --text-color: #ffffff;
}

html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
  background-color: var(--bg-color);
  color: var(--text-color);
}

.app-root {
  height: 100%;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* Element Plus dark theme unification */
.el-card {
  background: #151515 !important;
  border-color: #2a2a2a !important;
  color: #e5e7eb !important;
}

.el-card__body {
  color: #e5e7eb !important;
}

.el-table,
.el-table tr,
.el-table th.el-table__cell,
.el-table td.el-table__cell {
  background: #141414 !important;
  color: #e5e7eb !important;
  border-color: #2a2a2a !important;
}

.el-table th.el-table__cell {
  background: #1a1a1a !important;
  color: #c7c7c7 !important;
}

.el-table--enable-row-hover .el-table__body tr:hover > td.el-table__cell {
  background: #1d1d1d !important;
}

.el-input__wrapper,
.el-textarea__inner,
.el-select__wrapper {
  background: #121212 !important;
  box-shadow: 0 0 0 1px #2f2f2f inset !important;
  color: #f3f4f6 !important;
}

.el-input__inner,
.el-textarea__inner {
  color: #f3f4f6 !important;
}

.el-input__inner::placeholder,
.el-textarea__inner::placeholder {
  color: #737373 !important;
}

.el-button {
  background: #202020 !important;
  border-color: #343434 !important;
  color: #e5e7eb !important;
}

.el-button:hover {
  background: #2a2a2a !important;
  border-color: #444 !important;
}

.el-button.is-plain {
  background: #171717 !important;
}

.el-dialog {
  background: #171717 !important;
  border: 1px solid #2a2a2a !important;
}

.el-dialog__title,
.el-dialog__body,
.el-dialog__headerbtn .el-dialog__close {
  color: #e5e7eb !important;
}

.el-pagination {
  color: #c7c7c7 !important;
}

.el-pagination button,
.el-pager li {
  background: #171717 !important;
  color: #d1d5db !important;
}

.el-pager li.is-active {
  color: #ffffff !important;
  border: 1px solid #3a3a3a;
}
</style>
