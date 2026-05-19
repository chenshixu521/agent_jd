export function formatBytes(size: number): string {
  if (!size) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1)
  return `${(size / Math.pow(1024, index)).toFixed(1)} ${units[index]}`
}

export function formatDate(value?: string): string {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

export function statusText(status: number): string {
  return ({ 0: '等待中', 1: '运行中', 2: '成功', 3: '失败', 4: '已取消' } as Record<number, string>)[status] || '未知'
}
