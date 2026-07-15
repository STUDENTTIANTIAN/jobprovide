<template>
  <el-container>
    <el-header>
      <el-menu mode="horizontal" :router="true">
        <el-menu-item index="/">字幕任务</el-menu-item>
        <el-menu-item index="/media">素材库</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
</script>

<style>
body {
  margin: 0;
  padding: 0;
}
</style>
