module.exports = {
    devServer: {
        proxy: {
            '/api': {
                target: 'http://localhost:5000',
                changeOrigin: true,
                ws: true,
                secure: false,
                pathRewrite: {
                    '^/api': ''
                }
            }
        }
    }
}